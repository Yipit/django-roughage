from collections import defaultdict, Iterable
from django.contrib.admin.util import NestedObjects

class Dirt(object):
    
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
        
        self.new_objects[queryset.model._meta.db_table].update(queryset_ids)
        if not leaf:
            self.children = get_dependents(queryset)
            
            # for keep_obj in keep_objs:
            #     if isinstance(keep_obj, Iterable):
            #         self.add_queryset(keep_obj)
            #     else:
            #         self.add_queryset([keep_obj])

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
