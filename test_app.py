from coreapi.document import Document
from django.conf.urls import url
from django_coreapi.renderers import CoreAPIJSONRenderer
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response


@api_view(['GET'])
@renderer_classes([CoreAPIJSONRenderer])
def document(request):
    return Response(Document(title='Test Document', url='/'))


@api_view(['GET'])
@renderer_classes([CoreAPIJSONRenderer])
def headers(request):
    if not request.META.get('HTTP_AUTHORIZATION'):
        raise Exception('Missing header')
    return Response(Document(title='Test Document', url='/'))


urlpatterns = [
    url(r'^headers/$', headers),
    url('', document),
]
