import sys

from collections import defaultdict, Iterable
from django.contrib.admin.util import NestedObjects

from .utils import queryset_namespace, chunks, model_namespace, get_model_from_key
from django.db import models
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.loading import get_model
from django.db.models import Manager

class GrowthMeta(type):
    
    def __new__(cls, name, bases, attrs):
        model = attrs.get('model')
        if isinstance(model, basestring):
            app, model =  attrs.get('model').split(".")
            attrs['model'] = get_model(app, model)
        return super(GrowthMeta, cls).__new__(cls, name, bases, attrs)

SOIL = defaultdict(set)

class Dirt(object):
    
    CHUNK_SIZE = 100
    
    def __init__(self, database, seeds, branches):
        self.database = database
        self.soil = SOIL
        self.seeds = seeds
        self.branches = branches
    
    def __unicode__(self):
        return u"Dirt: %s" % self.soil
    
    def start_growing(self):
        for seed_model, seed_class in self.seeds.iteritems():
            seed = seed_class(database=self.database, branches=self.branches)
            seed.grow()
    
    def harvest(self):#, format, indent):
        format = "json"
        for key, pk_set in self.soil.iteritems():
            model = get_model_from_key(key)
            key = model_namespace(model)
            
            if self.seeds.get(key):
                wash_func = self.seeds.get(key).wash
            elif self.branches.get(key):
                wash_func = self.branches.get(key).wash
            else:
                wash_func = None
            for chunk in chunks(list(pk_set), self.CHUNK_SIZE):
                objects = model._default_manager.using(self.database).filter(pk__in=chunk)
                if wash_func:
                    for obj in objects:
                        wash_func(obj)
                data = serializers.serialize(format, objects, ensure_ascii=True, indent=2)
                yield data

class BaseGrowth(object):
    
    __metaclass__ = GrowthMeta
    
    soil = SOIL
    wash = None
    
    def __init__(self, database, seeds, branches, parent_model=None, ids_from_parent=None):
        self.database = database
        self.seeds = seeds
        self.branches = branches
    
    def __unicode__(self):
        return u"%s" % self.__class__.__name__
    
    def get_branches(self, obj):
        
        model = obj.__class__
        related_objects = model._meta.get_all_related_objects()
        branches = {}
        for related_object in related_objects:
            related_model = related_object.model
            key = model_namespace(related_model)
            branch = self.branches.get(key)
            if branch:
                branches[related_object.get_accessor_name()] = branch
        
        return branches
    
    def add_depends_on(self, obj):
        fields_to_get = [field.name for field in obj._meta.fields if isinstance(field, models.ForeignKey)]
        dependant_on = [getattr(obj, name) for name in fields_to_get]
        for _obj in dependant_on:
            if _obj:
                self.add_to_soil(_obj)
        
        # Only follow m2ms for models with branches or seeds
        if obj.__class__ == self.model:
            m2ms = obj._meta.many_to_many
            for m2m in m2ms:
                auto_created = m2m.rel.through._meta.auto_created
                objs = getattr(obj, m2m.name)
                for _obj in objs.using(self.database).all():
                    self.add_to_soil(_obj)
                # If the m2m through table was manually declared django serializes 
                # differently, so we need to account for that
                if not auto_created:
                    objs = m2m.rel.through.objects.using(self.database).filter(**{m2m.related_query_name(): obj})
                    for _obj in objs:
                        self.add_to_soil(_obj)
                    
        
        one2ones = [related.var_name for related in obj._meta.get_all_related_objects() if isinstance(related.field, models.OneToOneField)]
        for one2one in one2ones:
            try:
                _obj = getattr(obj, one2one)
            except ObjectDoesNotExist:
                continue
            else:
                self.add_to_soil(_obj)
    
    def add_to_soil(self, obj):
        
        key = model_namespace(obj)
        if obj.id in self.soil[key]:
            return
        self.soil[key].add(obj.id)
        self.add_depends_on(obj)
        branches = self.get_branches(obj)
        for name, branch in branches.items():
            branch(obj, name, self.branches).grow()
        
    def add_queryset(self, queryset):
        for obj in queryset:
            self.add_to_soil(obj)


class Seed(BaseGrowth):
    
    querysets = []
    
    def __init__(self, database, branches):
        self.database = database
        self.branches = branches
    
    def grow(self):
        print >> sys.stderr, "Growing", unicode(self)
        for queryset in self.querysets:
            self.add_queryset(queryset)

class Branch(BaseGrowth):
    
    def __init__(self, database, parent, name, branches):
        self.database = database
        self.parent = parent
        self.name = name
        self.branches = branches
    
    def grow(self):
        
        # Get the related object or manager
        try:
            base = getattr(self.parent, self.name)
        except ObjectDoesNotExist:
            # if we get an ObjectDoesNotExists, it was a OneToOne
            # that doesn't actually exist in the database
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
