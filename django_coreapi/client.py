from coreapi import Client
from coreapi.client import _lookup_link
from coreapi.compat import string_types
from coreapi.document import Link
from coreapi.transports import determine_transport
from django_coreapi.transports import DjangoTestHTTPTransport


def _make_absolute(url):
    if not url.startswith('http'):
        url = 'http://testserver/' + url.lstrip('/')
    return url


class DjangoCoreAPIClient(Client):
    def __init__(self, decoders=None, transports=None):
        if not transports:
            transports = [DjangoTestHTTPTransport()]
        super(DjangoCoreAPIClient, self).__init__(decoders, transports)

    def get(self, url):
        url = _make_absolute(url)
        link = Link(url, action='get')

        # Perform the action, and return a new document.
        transport = determine_transport(link.url, transports=self.transports)
        return transport.transition(link, decoders=self.decoders)

    def reload(self, document):
        url = _make_absolute(document.url)
        link = Link(url, action='get')

        # Perform the action, and return a new document.
        transport = determine_transport(link.url, transports=self.transports)
        return transport.transition(link, decoders=self.decoders)

    def action(self, document, keys, params=None, action=None, inplace=None):
        if isinstance(keys, string_types):
            keys = [keys]

        # Validate the keys and link parameters.
        link, link_ancestors = _lookup_link(document, keys)
        url = _make_absolute(link.url)

        if (action is not None) or (inplace is not None):
            # Handle any explicit overrides.
            action = link.action if (action is None) else action
            inplace = link.inplace if (inplace is None) else inplace
            link = Link(url, action, inplace, link.fields)
        else:
            link = Link(url, link.action, link.inplace, link.fields)

        # Perform the action, and return a new document.
        transport = determine_transport(url, transports=self.transports)
        return transport.transition(link, params, decoders=self.decoders, link_ancestors=link_ancestors)
