import base64

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            image_format, image_str = data.split(';base64,')
            ext = image_format.split('/')[-1]

            data = ContentFile(base64.b64decode(image_str), name='temp.' + ext)

        return super().to_internal_value(data)
