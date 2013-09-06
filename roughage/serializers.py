import json
from django.core.serializers.json import PythonSerializer, DjangoJSONEncoder
from django.utils.encoding import smart_unicode

from roughage.utils import model_namespace

DIRT = 'dirt'


# copy from Django commit d7dfab59ead97b35c6f6786784225f377783e376
class JSONSerializer(PythonSerializer):
    """
    Convert a queryset to JSON.
    """
    internal_use_only = False

    def end_serialization(self):
        if json.__version__.split('.') >= ['2', '1', '3']:
            # Use JS strings to represent Python Decimal instances (ticket #16850)
            self.options.update({'use_decimal': False})
        json.dump(self.objects, self.stream, cls=DjangoJSONEncoder, **self.options)

    def getvalue(self):
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()


class Serializer(JSONSerializer):

    def serialize(self, queryset, **options):
        if DIRT not in options:
            raise ValueError("You must pass `dirt` in to use the RoughageSerializer")
        self.dirt = options.pop(DIRT)
        return super(Serializer, self).serialize(queryset, **options)

    def handle_m2m_field(self, obj, field):
        if field.rel.through._meta.auto_created:
            if self.use_natural_keys and hasattr(field.rel.to, 'natural_key'):
                m2m_value = lambda value: value.natural_key()
            else:
                m2m_value = lambda value: smart_unicode(value._get_pk_val(), strings_only=True)
            dirt_key = model_namespace(field.rel.to)
            dirt = self.dirt
            obj_set = dirt.soil.objects.get(dirt_key, set())
            self._current[field.name] = [m2m_value(related)
                               for related in getattr(obj, field.name).iterator() if related.pk in obj_set]
