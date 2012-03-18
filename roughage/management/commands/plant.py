import sys

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.importlib import import_module
CONFIG_NAME = 'seeds'

from roughage.base import Branch, Seed, Dirt
from roughage.utils import model_namespace


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-d", "--database", dest="database", default="default", help='The database name to pull data from'),
    )
    
    def handle(self, *args, **options):
        self.seeds = {}
        self.branches = {}
        self.database = options.get('database', "default")
        
        apps = settings.INSTALLED_APPS
        for app in apps:
            self.process_app(app)
        try:
            seeds = import_module('seeds')
        except ImportError:
            pass
        else:
            self.process_module(seeds)
        print >> sys.stderr, "Preparing to plant..."
        print >> sys.stderr, "\tSeeds: %s" % self.seeds.values()
        print >> sys.stderr, "\tBranches: %s" % self.branches.values()
        print >> sys.stderr, "Now Growing..."
        
        dirt = Dirt(self.database, self.seeds, self.branches)
        dirt.start_growing()
        dirt.print_soil()
        sys.stdout.write("[")
        first = True
        for objects in dirt.harvest():
            if not first:
                sys.stdout.write(',')
            sys.stdout.write(objects[1:-1])
            first = False
        sys.stdout.write("]")
        sys.stderr.write('\n')
        
    def process_module(self, module):
        seeds = {}
        branches = {}
        real_clazzes = [clazz for clazz in dir(module) if not clazz.startswith("__")]
        for name in real_clazzes:
            obj = getattr(module, name)
            if (obj != Seed) and issubclass(obj, Seed):
                seeds[model_namespace(obj.model)] = obj
            elif (obj != Branch) and issubclass(obj, Branch):
                branches[model_namespace(obj.model)] = obj
        self.seeds.update(seeds)
        self.branches.update(branches)
    
    def process_app(self, app):
        # Attempt to import the app's seed module.
        try:
            module = import_module('%s.%s' % (app, CONFIG_NAME))
        except ImportError:
            pass
        else:
            self.process_module(module)
