from django.core.serializers import register_serializer

register_serializer('roughage', 'roughage.serializers')

from roughage.base import Seed

__all__ = [Seed]
