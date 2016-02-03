from coreapi import Link, Document
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.serializers import Serializer


class CoreLinkField(serializers.HyperlinkedRelatedField):
    def __init__(self, action=None, fields=None, source='pk', transition=None, **kwargs):
        self.action = action
        self.fields = fields or []
        self.transition = transition
        super(CoreLinkField, self).__init__(read_only=True, source=source, **kwargs)

    def to_internal_value(self, data):
        return super(CoreLinkField, self).to_internal_value(data)

    def to_representation(self, value):
        url = super(CoreLinkField, self).to_representation(value)
        return Link(url=url, action=self.action, fields=self.fields, transition=self.transition)


class CoreAPIDocumentSerializer(Serializer):
    @property
    def data(self):
        return super(Serializer, self).data

    def get_title(self, instance):
        raise NotImplementedError()

    def to_representation(self, instance):
        data = super(CoreAPIDocumentSerializer, self).to_representation(instance)
        try:
            url = data.pop('url')
        except KeyError:
            raise APIException('A \'url\' field is required to serialize as a Document')
        return Document(
            title=self.get_title(instance),
            url=url,
            content=data,
        )
