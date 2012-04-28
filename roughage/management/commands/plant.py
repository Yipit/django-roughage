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
        make_option("-f", "--file", dest="dest_file", default=None, help='The filename to put data in'),
        make_option("-s", "--seeds", dest="seeds_module", default='seeds', help='The seeds module'),
    )
    
    def handle(self, *args, **options):
        self.seeds = {}
        self.branches = {}
        self.database = options.get('database')
        
        verbosity = int(options.get('verbosity', 1))
        
        seed_module = options.get('seeds_module')
        stream = self.get_stream(options)
        
        apps = settings.INSTALLED_APPS
        for app in apps:
            self.process_app(app)
        try:
            seeds = import_module(seed_module)
        except ImportError:
            pass
        else:
            self.process_module(seeds)
        
        if verbosity > 1:
            print >> sys.stderr, "Preparing to plant..."
            print >> sys.stderr, "\tSeeds: %s" % self.seeds.values()
            print >> sys.stderr, "\tBranches: %s" % self.branches.values()
            print >> sys.stderr, "Now Growing..."
        
        dirt = Dirt(self.database, self.seeds, self.branches)
        dirt.start_growing()
        dirt.print_soil(verbosity)
        dirt.harvest(stream)
    
    def get_stream(self, options):
        
        # command was called programatically.
        # return the stream the was passed in
        if options.get('stream'):
            return options.get('stream')
        
        if options.get('dest_file'):
            return open(dest_file, 'w')
            
        else:
            return sys.stdout
    
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
