from collections import defaultdict, Iterable
from django.contrib.admin.util import NestedObjects

from .utils import queryset_namespace, chunks
from django.db.models.loading import get_model
from django.core import serializers

class Dirt(object):
    
    CHUNK_SIZE = 100
    
    def __init__(self, seeds, branches, leaves):
        self.soil = defaultdict(set)
        self.seeds = seeds
        self.branches = branches
        self.leaves = leaves
    
    def __unicode__(self):
        return u"Dirt: %s" % self.soil
    
    def start_growing(self):
        print "Planting some seeds"
        for seed_model, seed_class in self.seeds.iteritems():
            seed = seed_class()
            new_objects, children = seed.grow()
            self.soil.update(new_objects)
    
    def _get_model_from_soil_key(self, key):
        app, model = key.split(".")
        return get_model(app, model)
        
    def harvest(self):#, format, indent):
        format = "json"
        for key, pk_set in self.soil.iteritems():
            model = self._get_model_from_soil_key(key)
            for chunk in chunks(list(pk_set), self.CHUNK_SIZE):
                objects = model._default_manager.filter(pk__in=chunk)
                yield serializers.serialize(format, objects)
                
            



class BaseSeed(object):
    def __init__(self):
        self.new_objects = defaultdict(set)
        self.children = defaultdict(set)
    
    def grow(self):
        print "\tProcessing seed", self
        for queryset in self.querysets:
            self.add_queryset(queryset)
        return self.new_objects, self.children


    def add_queryset(self, queryset):
        # TODO determine if leaf based on object model
        leaf = False
        queryset_ids = [obj.id for obj in queryset]
        
        self.new_objects[queryset_namespace(queryset)].update(queryset_ids)
        if not leaf:
            self.children = get_dependents(queryset)


class Seed(BaseSeed):
    def seed_instances(self):
        return self.queryset


class Branch(BaseSeed):
    pass


class Leaf(BaseSeed):
    pass


def get_dependents(queryset):
    # Get all dependent objects and add
    collect = NestedObjects('default')
    collect.collect(queryset)
    result = collect.nested()
    # TODO this lists objects that need this obj, but not necessarily are sufficient with this obj
    try:
        return result[1]
    except IndexError:
        return []
