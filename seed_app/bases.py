from collections import defaultdict, Iterable
from django.contrib.admin.util import NestedObjects

from .utils import queryset_namespace, chunks, model_namespace, get_model_from_key
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
            seed = seed_class(seeds=self.seeds, branches=self.branches, leaves=self.leaves)
            new_objects = seed.grow()
            self.soil.update(new_objects)
    
    def harvest(self):#, format, indent):
        format = "json"
        for key, pk_set in self.soil.iteritems():
            model = get_model_from_key(key)
            for chunk in chunks(list(pk_set), self.CHUNK_SIZE):
                objects = model._default_manager.filter(pk__in=chunk)
                yield serializers.serialize(format, objects)

class BaseSeed(object):
    def __init__(self, seeds, branches, leaves, parent_model=None, queryset_from_parent=None):
        self.seeds = seeds
        self.branches = branches
        self.leaves = leaves
        
        self.parent_model = parent_model
        self.queryset_from_parent = queryset_from_parent
        
        self.new_objects = defaultdict(set)
        self.children = defaultdict(set)
    
    def get_growth(self, model):
        "Returns a seed, branch, or leaf class for the model."
        return self.seeds.get(model) or self.branches.get(model) or self.leaves.get(model)
    
    def add_queryset(self, queryset):
        # TODO determine if leaf based on object model
        leaf = False
        queryset_ids = [obj.id for obj in queryset]
        
        self.new_objects[queryset_namespace(queryset)].update(queryset_ids)
        if not leaf:
            self.children = get_dependents(queryset)
    
    def grow(self):
        print "\tProcessing seed", self
        if self.querysets:
            # Seeds
            for queryset in self.querysets:
                self.add_queryset(queryset)
        else:
            # Branches, Leaves
            print 'no branches yet'
            #import pdb;pdb.set_trace()
        
        
        # self.children = { 'deal.Deal' : set(<deal1>, <deal5>), 'event.Event': set(<event3>, <event7>)}
        for child_model, child_set in self.children.iteritems():
            growth = self.get_growth(child_model)
            if not growth:
                continue
            
            child_growth = growth(seeds=self.seeds, branches=self.branches, leaves=self.leaves, parent_model=self.model, queryset_from_parent=child_set)
            child_growth.grow()
        return self.new_objects



class Seed(BaseSeed):
    def seed_instances(self):
        return self.queryset


class Branch(BaseSeed):
    def reduce_geo__city(self, query):
        return query.published()
    
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
        dependents = result[1]
    except IndexError:
        dependents = []
    dependent_model_map = defaultdict(set)
    flat_dependents = []
    for dependent in dependents:
        if isinstance(dependent, Iterable):
            flat_dependents.extend(dependent)
        else:
            flat_dependents.append(dependent)
    for flat_dependent in flat_dependents:
        dependent_model_map[model_namespace(flat_dependent)].add(flat_dependent)
    return dependent_model_map
