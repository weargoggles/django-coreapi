from coreapi import Client
from coreapi.client import _lookup_link
from coreapi.compat import string_types
from coreapi.document import Link
from coreapi.utils import determine_transport
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
        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, decoders=self.decoders)

    def reload(self, document):
        url = _make_absolute(document.url)
        link = Link(url, action='get')

        # Perform the action, and return a new document.
        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, decoders=self.decoders)

    def action(self, document, keys, params=None, action=None, encoding=None, transform=None):
        if isinstance(keys, string_types):
            keys = [keys]

        # Validate the keys and link parameters.
        link, link_ancestors = _lookup_link(document, keys)
        url = _make_absolute(link.url)

        if (action is not None) or (encoding is not None) or (transform is not None):
            # Handle any explicit overrides.
            action = link.action if (action is None) else action
            encoding = link.encoding if (encoding is None) else encoding
            transform = link.transform if (transform is None) else transform
            link = Link(url, action=action, encoding=encoding, transform=transform, fields=link.fields)

        # Perform the action, and return a new document.
        transport = determine_transport(self.transports, url)
        return transport.transition(link, params, decoders=self.decoders, link_ancestors=link_ancestors)
