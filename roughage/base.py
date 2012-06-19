import sys
from collections import defaultdict

from django.db import models
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.loading import get_model
from django.db.models import Manager

from .utils import chunks, model_namespace, get_model_from_key


class SeedMeta(type):

    def __new__(cls, name, bases, attrs):
        model = attrs.get('model')
        if isinstance(model, basestring):
            app, model = attrs.get('model').split(".")
            attrs['model'] = get_model(app, model)
        return super(SeedMeta, cls).__new__(cls, name, bases, attrs)


class Soil(object):

    def __init__(self):
        self.reset()

    def reset(self):
        """Used in tests to reset global SOIL obj"""
        self.objects = defaultdict(set)
        self.seeded = defaultdict(set)
        self.trees = []

SOIL = Soil()


class Dirt(object):

    CHUNK_SIZE = 100

    def __init__(self, database, seeds):
        self.database = database
        self.soil = SOIL
        self.seeds = seeds

    def __unicode__(self):
        return u"Dirt: %s" % self.soil

    def start_growing(self):
        for seed_model, seed_class in self.seeds.iteritems():
            seed = seed_class(database=self.database, seeds=self.seeds)
            seed.grow()

    def print_soil(self, verbosity):
        if not verbosity > 1:
            return
        print >> sys.stderr, "The following have been planted:"
        sorted_keys = sorted(self.soil.objects.keys())
        for key in sorted_keys:
            object_count = len(self.soil.objects[key])
            print >> sys.stderr, "\t%s:%s" % (key, object_count)

    def _harvest(self):
        format = "roughage"
        for key, pk_set in self.soil.objects.iteritems():
            model = get_model_from_key(key)
            key = model_namespace(model)

            if self.seeds.get(key):
                wash_func = self.seeds.get(key).wash
            else:
                wash_func = None
            for chunk in chunks(list(pk_set), self.CHUNK_SIZE):
                objects = model._default_manager.using(self.database).filter(pk__in=chunk)
                if wash_func:
                    for obj in objects:
                        wash_func(obj)
                data = serializers.serialize(format, objects, ensure_ascii=True, indent=2, dirt=self)
                yield data

    def harvest(self, stream):
        stream.write("[")
        for index, objects in enumerate(self._harvest()):
            if index:
                stream.write(',')
            stream.write(objects[1:-1])
        stream.write("]")
        stream.write('\n')


class Seed(object):

    __metaclass__ = SeedMeta

    soil = SOIL
    wash = None

    def __init__(self, database, seeds, name=None, parent=None, ids_from_parent=None):
        self.database = database
        self.seeds = seeds
        self.parent = parent
        self.name = name

    def __unicode__(self):
        return u"%s" % self.__class__.__name__

    def querysets(self):
        return []

    def grow(self):
        for queryset in self.querysets():
            self.add_queryset(queryset)

    def add_queryset(self, queryset):
        """
        Add all objs in the queryset to the soil
        """
        for obj in queryset.using(self.database):
            self.add_to_soil(obj)

    def get_related_seeds(self, obj):
        """
        Return seeds for classes that ForeignKey to obj
        """

        model = obj.__class__
        related_objects = model._meta.get_all_related_objects()
        seeds = {}
        for related_object in related_objects:
            related_model = related_object.model
            key = model_namespace(related_model)
            seed = self.seeds.get(key)
            if seed:
                seeds[related_object.get_accessor_name()] = seed

        return seeds

    def add_depends_on(self, obj, add_m2ms=False):
        """
        Get all obects that obj depends on.

        If obj is an instance on the model for the current Seed,
        follow m2m relationships. Otherwise, don't get the m2m'd
        models neccessarily
        """

        self.add_dependants(obj)

        # Only follow m2ms for models with seeds
        if add_m2ms or obj.__class__ == self.model:
            self.add_m2ms(obj)

        self.add_one2ones(obj)

    def add_dependants(self, obj):
        fields_to_get = [field.name for field in obj._meta.fields
                                    if isinstance(field, models.ForeignKey)]
        dependant_on = [getattr(obj, name) for name in fields_to_get]
        for _obj in dependant_on:
            if _obj:
                self.add_to_soil(_obj)

    def add_m2ms(self, obj):
        m2ms = obj._meta.many_to_many
        for m2m in m2ms:
            capture_m2m_objects = True
            capture_join = False
            if m2m.rel.to == obj.__class__:
                capture_m2m_objects = False
                capture_join = True
            if not capture_join:
                capture_join = m2m.rel.through._meta.auto_created
            if capture_m2m_objects:
                objs = getattr(obj, m2m.name)
                for _obj in objs.using(self.database).all():
                    self.add_to_soil(_obj)
            # If the m2m through table was manually declared django serializes
            # differently, so we need to account for that
            if not capture_join:
                objs = m2m.rel.through.objects.using(self.database).filter(**{m2m.related_query_name(): obj})
                for _obj in objs:
                    self.add_to_soil(_obj)

    def add_one2ones(self, obj):
        one2ones = [related.get_accessor_name()
                    for related in obj._meta.get_all_related_objects()
                    if isinstance(related.field, models.OneToOneField)
                ]
        for one2one in one2ones:
            try:
                _obj = getattr(obj, one2one)
            except ObjectDoesNotExist:
                continue
            else:
                if _obj is not None:
                    self.add_to_soil(_obj)

    def add_to_soil(self, obj):
        """
        Put obj in the soil for the correct name space
        for later retrieval and serialization
        """

        key = model_namespace(obj)
        if obj.id in self.soil.objects[key]:
            return

        self.soil.objects[key].add(obj.id)
        if key in self.seeds and not obj.id in self.soil.seeded[key]:
            self.soil.seeded[key].add(obj.id)
            add_m2ms = True
        else:
            add_m2ms = False

        self.add_depends_on(obj, add_m2ms)
        seeds = self.get_related_seeds(obj)
        for name, seed in seeds.items():
            seed(database=self.database, seeds=self.seeds, name=name, parent=obj).branch_out()

    def branch_out(self):
        """
        Grow out all of the objects that depend on self.parent
        """

        # Get the related object or manager
        try:
            base = getattr(self.parent, self.name)
        except ObjectDoesNotExist:
            # if we get an ObjectDoesNotExists, it was a OneToOne
            # that doesn't actually exist in the database
            return

        # Exception for OneToOneField that returns None
        if base is None:
            return

        # If base is a manager, try to reduce the query
        if isinstance(base, Manager):
            base_manager = base.using(self.database).all()
            try:
                reducer = getattr(self, "trim_%s" % model_namespace(self.parent))
            except AttributeError:
                reducer = lambda queryset: queryset.none()

            queryset = reducer(base_manager)
            self.add_queryset(queryset)
        # Otherwise base is a object from the OneToOne relation
        # so add it to the soil
        else:
            self.add_to_soil(base)
