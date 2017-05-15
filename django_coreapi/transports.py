from __future__ import unicode_literals
from collections import OrderedDict
from coreapi import codecs
from coreapi.document import Document, Object, Link, Array, Error

from coreapi.utils import negotiate_decoder
from coreapi.exceptions import ErrorMessage
from coreapi.transports.http import HTTPTransport
from rest_framework.test import APIClient
import json
import uritemplate
try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse


def _get_http_method(action):
    if not action:
        return 'GET'
    return action.upper()


def _separate_params(method, fields, params=None):
    """
    Separate the params into their location types: path, query, or form.
    """
    if params is None:
        return ({}, {}, {}, {})

    field_map = {field.name: field for field in fields}
    path_params = {}
    query_params = {}
    body_params = {}
    header_params = {}
    for key, value in params.items():
        if key not in field_map or not field_map[key].location:
            # Default is 'query' for 'GET'/'DELETE', and 'form' others.
            location = 'query' if method in ('GET', 'DELETE') else 'form'
        else:
            location = field_map[key].location

        if location == 'path':
            path_params[key] = value
        elif location == 'query':
            query_params[key] = value
        elif location == 'header':
            header_params[key] = value
        elif location == 'body':
            body_params = value
        else:
            body_params[key] = value

    return path_params, query_params, body_params, header_params


def _expand_path_params(url, path_params):
    """
    Given a templated URL and some parameters that have been provided,
    expand the URL.
    """
    if path_params:
        return uritemplate.expand(url, path_params)
    return url


def _get_headers(url, decoders=None, credentials=None):
    """
    Return a dictionary of HTTP headers to use in the outgoing request.
    """
    if decoders is None:
        decoders = codecs

    accept = ', '.join([decoder.media_type for decoder in decoders])

    headers = {
        'accept': accept,
        'user-agent': 'coreapi'
    }

    if credentials:
        # Include any authorization credentials relevant to this domain.
        url_components = urlparse.urlparse(url)
        host = url_components.hostname
        if host in credentials:
            headers['authorization'] = credentials[host]

    return headers


def _handle_transform_replacements(document, link, link_ancestors):
    """
    Given a new document, and the link/ancestors it was created,
    determine if we should:
    * Make an inline replacement and then return the modified document tree.
    * Return the new document as-is.
    """
    if link.transform is None:
        transform = link.action.lower() in ('put', 'patch', 'delete')
    else:
        transform = link.transform

    if transform:
        root = link_ancestors[0].document
        keys_to_link_parent = link_ancestors[-1].keys
        if document is None:
            return root.delete_in(keys_to_link_parent)
        return root.set_in(keys_to_link_parent, document)

    return document


def _coerce_to_error_content(node):
    """
    Errors should not contain nested documents or links.
    If we get a 4xx or 5xx response with a Document, then coerce
    the document content into plain data.
    """
    if isinstance(node, (Document, Object)):
        # Strip Links from Documents, treat Documents as plain dicts.
        return OrderedDict([
            (key, _coerce_to_error_content(value))
            for key, value in node.data.items()
        ])
    elif isinstance(node, Array):
        # Strip Links from Arrays.
        return [
            _coerce_to_error_content(item)
            for item in node
            if not isinstance(item, Link)
        ]
    return node


def _coerce_to_error(obj, default_title):
    """
    Given an arbitrary return result, coerce it into an Error instance.
    """
    if isinstance(obj, Document):
        return Error(
            title=obj.title or default_title,
            content=_coerce_to_error_content(obj)
        )
    elif isinstance(obj, dict):
        return Error(title=default_title, content=obj)
    elif isinstance(obj, list):
        return Error(title=default_title, content={'messages': obj})
    elif obj is None:
        return Error(title=default_title)
    return Error(title=default_title, content={'message': obj})


def _make_http_request_with_test_client(url, method, headers, query_params, form_params):
    client = APIClient()

    opts = {'follow': True}

    if query_params:
        opts['data'] = query_params
    elif form_params:
        opts['data'] = json.dumps(form_params)
        opts['content_type'] = 'application/json'

    for key, value in headers.items():
        opts['HTTP_{}'.format(key.upper())] = value

    func = getattr(client, method.lower())
    return func(url, **opts)


def _decode_result_from_test_client(response, decoders=None, original_url=None):
    """
    Given an HTTP response, return the decoded Core API document.
    """
    if response.content:
        if response.redirect_chain:
            base_url = response.redirect_chain[-1][0]
        else:
            base_url = original_url
        # Content returned in response. We should decode it.
        content_type = response.get('content-type')
        codec = negotiate_decoder(decoders, content_type)
        result = codec.load(response.content, base_url=base_url)
    else:
        # No content returned in response.
        result = None

    # Coerce 4xx and 5xx codes into errors.
    is_error = response.status_code >= 400 and response.status_code <= 599
    if is_error and not isinstance(result, Error):
        result = _coerce_to_error(result, default_title=response.reason_phrase)

    return result


class DjangoTestHTTPTransport(HTTPTransport):

    def transition(self, link, params=None, decoders=None, link_ancestors=None):
        method = _get_http_method(link.action)
        path_params, query_params, body_params, header_params = _separate_params(method, link.fields, params)
        url = _expand_path_params(link.url, path_params)
        headers = _get_headers(url, decoders, self._session.auth)
        headers.update(self.headers)
        response = _make_http_request_with_test_client(url, method, headers, query_params, body_params)
        result = _decode_result_from_test_client(response, decoders, url)

        if isinstance(result, Document) and link_ancestors:
            result = _handle_transform_replacements(result, link, link_ancestors)

        if isinstance(result, Error):
            raise ErrorMessage(result)

        return result
