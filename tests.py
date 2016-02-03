import unittest
from django.conf import settings
settings.configure(ROOT_URLCONF='test_app', DEBUG=True, REST_FRAMEWORK={'UNAUTHENTICATED_USER': None})
import django
django.setup()
from django_coreapi.client import DjangoCoreAPIClient


class Tests(unittest.TestCase):
    def test_client(self):
        client = DjangoCoreAPIClient()
        doc = client.get('/')
        self.assertIsNotNone(doc)
