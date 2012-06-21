__title__ = 'django-roughage'
__version__ = '0.0.7'


from django.core.serializers import register_serializer

register_serializer('roughage', 'roughage.serializers')

from roughage.base import Seed

__all__ = [Seed]
