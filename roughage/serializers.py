from django.core.serializers.json import Serializer as JSONSerializer
from django.utils.encoding import smart_unicode

from roughage.utils import model_namespace, is_django_version_greater_than

DIRT = 'dirt'


class Serializer(JSONSerializer):

    def serialize(self, queryset, **options):
        if DIRT not in options:
            raise ValueError("You must pass `dirt` in to use the RoughageSerializer")
        self.dirt = options.pop(DIRT)
        return super(Serializer, self).serialize(queryset, **options)

    def handle_m2m_field(self, obj, field):
        if field.rel.through._meta.auto_created:
            if hasattr(self, 'use_natural_keys') and self.use_natural_keys and hasattr(field.rel.to, 'natural_key'):
                m2m_value = lambda value: value.natural_key()
            else:
                m2m_value = lambda value: smart_unicode(value._get_pk_val(), strings_only=True)
            dirt_key = model_namespace(field.rel.to)
            dirt = self.dirt
            obj_set = dirt.soil.objects.get(dirt_key, set())
            self._current[field.name] = [m2m_value(related)
                               for related in getattr(obj, field.name).iterator() if related.pk in obj_set]

    """
    Django 1.5+ Serializer.serialize() return value looks like this:

        [
        {
          "pk": 1,
          "model": "app.author",
          "fields": {
            "first_name": "Bob",
            "last_name": "Johnson"
          }
        }
        ]

    But this is not compatible with Django 1.4 code, since the structure is different.
    Since django-roughage was written for Django 1.4, but needs to support Django 1.5,
    the return value needs to be slightly modificated to look like this:

        {
            "pk": 1,
            "model": "app.author",
            "fields": {
                "first_name": "Bob",
                "last_name": "Johnson"
            }
        }

    And that's why start_serialization() and end_serialization() were overridden
    """

    def start_serialization(self):
        super(Serializer, self).start_serialization()
        if is_django_version_greater_than("1.5"):
            # remove "[" from start
            self._remove_last_char_from_stream()

    def end_serialization(self):
        super(Serializer, self).end_serialization()
        if is_django_version_greater_than("1.5"):
            # remove "\n"
            if self.options.get("indent"):
                self._remove_last_char_from_stream()
            # remove "]"
            self._remove_last_char_from_stream()

    def _remove_last_char_from_stream(self):
        self.stream.seek(self.stream.pos - 1)
        self.stream.buf = self.stream.buf[:-1]
