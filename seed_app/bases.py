import sys

from collections import defaultdict, Iterable
from django.contrib.admin.util import NestedObjects

from .utils import queryset_namespace, chunks, model_namespace, get_model_from_key
from django.db import models
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.loading import get_model

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
            key = model_namespace(model)
            
            if self.seeds.get(key):
                wash_func = self.seeds.get(key).wash
            elif self.branches.get(key):
                wash_func = self.branches.get(key).wash
            else:
                wash_func = None
            for chunk in chunks(list(pk_set), self.CHUNK_SIZE):
                objects = model._default_manager.filter(pk__in=chunk)
                if wash_func:
                    for obj in objects:
                        wash_func(obj)
                data = serializers.serialize(format, objects, ensure_ascii=True, indent=2)
                yield data

class BaseGrowth(object):
    
    __metaclass__ = GrowthMeta
    
    soil = SOIL
    
    wash = None
    
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
            if obj.__class__ == self.model:
                objs = getattr(obj, m2m.name)
                for _obj in objs.all(): 
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
        if obj.id in self.soil[model_namespace(obj)]:
            return
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
        for queryset in self.querysets:
            self.add_queryset(queryset)

class Branch(BaseGrowth):
    
    def __init__(self, parent, name, branches):
        self.parent = parent
        self.name = name
        self.branches = branches
    
    def grow(self):
        base_manager = getattr(self.parent, self.name).all()
        try:
            reducer = getattr(self, "trim_%s" % model_namespace(self.parent))
        except AttributeError:
            reducer = lambda queryset: queryset.none()
        
        queryset = reducer(base_manager)
        self.add_queryset(queryset)
