import unittest
from coreapi import Document, Field, Link
from django.conf import settings
settings.configure(ROOT_URLCONF='test_app', DEBUG=True, REST_FRAMEWORK={'UNAUTHENTICATED_USER': None})
import django
django.setup()
from django_coreapi import mock
from django_coreapi.client import DjangoCoreAPIClient
from django_coreapi.transports import DjangoTestHTTPTransport


class Tests(unittest.TestCase):
    def test_client(self):
        client = DjangoCoreAPIClient()
        doc = client.get('/')
        self.assertIsNotNone(doc)

    def test_client_headers(self):
        transport = DjangoTestHTTPTransport(headers={'authorization': 'token'})
        client = DjangoCoreAPIClient(transports=[transport])
        doc = client.get('/headers/')
        self.assertIsNotNone(doc)

    def test_post_data(self):
        content = {
            'test': {
                'post_data': Link(url='/post_data/', action='post', fields=[
                    Field('data', location='body')
                ]),
            }
        }
        schema = Document(title='test', content=content)

        client = DjangoCoreAPIClient()
        doc = client.action(schema, ['test', 'post_data'], params={'data': {
            'test': 'cat'
        }})
        self.assertIsNotNone(doc)

    @mock.activate
    def test_mocking(self):
        content = {
            'test': {
                'post_data': Link(url='/post_data/', action='post', fields=[
                    Field('data', location='body')
                ]),
            }
        }
        schema = Document(title='test', content=content)
        mock.add(schema, ['test', 'post_data'], {"a": 1})
        client = DjangoCoreAPIClient()
        doc = client.action(schema, ['test', 'post_data'], params={'data': {
            'test': 'cat'
        }})
        self.assertEqual(doc, {"a": 1})
