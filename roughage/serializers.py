from django.core.serializers.json import Serializer as JSONSerializer
from django.utils.encoding import smart_unicode

from roughage.utils import model_namespace

DIRT = 'dirt'

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
            obj_set = dirt.soil.objects[dirt_key]
            self._current[field.name] = [m2m_value(related)
                               for related in getattr(obj, field.name).iterator() if related.id in obj_set]
    