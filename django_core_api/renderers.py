from coreapi.codecs import HTMLCodec, CoreJSONCodec
from rest_framework.renderers import BaseRenderer


class CoreAPIJSONRenderer(BaseRenderer):
    media_type = 'application/vnd.coreapi+json'

    def render(self, data, media_type=None, renderer_context=None):
        codec = CoreJSONCodec()
        return codec.dump(data, indent=True)


class CoreAPIHTMLRenderer(BaseRenderer):
    media_type = 'text/html'

    def render(self, data, media_type=None, renderer_context=None):
        codec = HTMLCodec()
        return codec.dump(data)
