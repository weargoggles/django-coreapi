import unittest
from django.conf import settings
settings.configure(ROOT_URLCONF='test_app', DEBUG=True, REST_FRAMEWORK={'UNAUTHENTICATED_USER': None})
import django
django.setup()
from django_coreapi.client import DjangoCoreAPIClient
from django_coreapi.transports import DjangoTestHTTPTransport


class Tests(unittest.TestCase):
    def test_client(self):
        client = DjangoCoreAPIClient()
        doc = client.get('/')
        self.assertIsNotNone(doc)

    def test_client_headers(self):
        client = DjangoCoreAPIClient()
        transport = DjangoTestHTTPTransport(headers={'authorization': 'token'})
        client = DjangoCoreAPIClient(transports=[transport])
        doc = client.get('/headers/')
        self.assertIsNotNone(doc)
