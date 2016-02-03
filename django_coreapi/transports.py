from coreapi.transports.http import (
    HTTPTransport, _get_http_method, _seperate_params, _expand_path_params,
    _get_headers, _handle_inplace_replacements, Document, negotiate_decoder,
    Error, ErrorMessage, _coerce_to_error)
from rest_framework.test import APIClient
import json


def _make_http_request_with_test_client(url, method, headers, query_params, form_params):
    client = APIClient()

    opts = {'follow': True}

    if query_params:
        opts['data'] = query_params
    elif form_params:
        opts['data'] = json.dumps(form_params)
        opts['CONTENT_TYPE'] = 'application/json'

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
        codec = negotiate_decoder(content_type, decoders=decoders)
        result = codec.load(response.content, base_url=base_url)
    else:
        # No content returned in response.
        result = None

    # Coerce 4xx and 5xx codes into errors.
    is_error = response.status_code >= 400 and response.status_code <= 599
    if is_error and not isinstance(result, Error):
        result = _coerce_to_error(result, default_title=response.reason)

    return result


class DjangoTestHTTPTransport(HTTPTransport):

    def transition(self, link, params=None, decoders=None, link_ancestors=None):
        method = _get_http_method(link.action)
        path_params, query_params, form_params = _seperate_params(method, link.fields, params)
        url = _expand_path_params(link.url, path_params)
        headers = _get_headers(url, decoders, self.credentials, self.headers)
        response = _make_http_request_with_test_client(url, method, headers, query_params, form_params)
        result = _decode_result_from_test_client(response, decoders, url)

        if isinstance(result, Document) and link_ancestors:
            result = _handle_inplace_replacements(result, link, link_ancestors)

        if isinstance(result, Error):
            raise ErrorMessage(result)

        return result
