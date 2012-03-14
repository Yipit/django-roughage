import sys

from collections import defaultdict, Iterable
from django.contrib.admin.util import NestedObjects

from .utils import queryset_namespace, chunks, model_namespace, get_model_from_key
from django.db import models
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist

SOIL = defaultdict(set)

class Dirt(object):
    CHUNK_SIZE = 100
    
    def __init__(self, seeds, branches):
        self.soil = SOIL
        self.seeds = seeds
        self.branches = branches
    
    def __unicode__(self):
        return u"Dirt: %s" % self.soil
    
    def start_growing(self):
        for seed_model, seed_class in self.seeds.iteritems():
            seed = seed_class(branches=self.branches)
            seed.grow()
    
    def harvest(self):#, format, indent):
        format = "json"
        for key, pk_set in self.soil.iteritems():
            model = get_model_from_key(key)
            for chunk in chunks(list(pk_set), self.CHUNK_SIZE):
                objects = model._default_manager.filter(pk__in=chunk)
                data = serializers.serialize(format, objects, ensure_ascii=False, indent=2)
                yield data

class BaseGrowth(object):
    
    soil = SOIL
    
    def __init__(self, seeds, branches, parent_model=None, ids_from_parent=None):
        self.seeds = seeds
        self.branches = branches
    
    def __unicode__(self):
        return u"%s" % self.__class__.__name__
    
    def get_branches(self):
        
        model = self.model
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
        
        m2ms = obj._meta.many_to_many
        
        for m2m in m2ms:
            model = m2m.related.parent_model
            if model_namespace(model) in self.branches:
                objs = getattr(obj, m2m.name)
                for _obj in objs.all():
                    self.add_to_soil(_obj)
    
    def add_to_soil(self, obj):
        self.soil[model_namespace(obj)].add(obj.id)
        self.add_depends_on(obj)
        
    def add_queryset(self, queryset):
        branches = self.get_branches()
        for obj in queryset:
            self.add_to_soil(obj)
            for name, branch in branches.items():
                branch(obj, name, self.branches).grow()


class Seed(BaseGrowth):
    
    querysets = []
    
    def __init__(self, branches):
        self.branches = branches
    
    def grow(self):
        print >> sys.stderr, "Growing", unicode(self)
        for queryset in self.querysets:
            self.add_queryset(queryset)

class Branch(BaseGrowth):
    
    def __init__(self, parent, name, branches):
        self.parent = parent
        self.name = name
        self.branches = branches
    
    def grow(self):
        print >> sys.stderr, "Growing", self.__class__.__name__
        base_manager = getattr(self.parent, self.name).all()
        try:
            reducer = getattr(self, "reduce_%s" % model_namespace(self.parent))
        except AttributeError:
            reducer = lambda queryset: queryset.none()
        
        queryset = reducer(base_manager)
        self.add_queryset(queryset)
