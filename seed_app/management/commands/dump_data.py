import inspect
import sys

from optparse import make_option

from django.db.models.loading import get_models, get_apps
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.importlib import import_module
CONFIG_NAME = 'seeds'

from seed_app.bases import Branch, Seed, Dirt
from seed_app.utils import model_namespace

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-d", "--delete", action="store_true", dest="delete", default=False, help='Disables Delete of Downloaded File'),
    )
    
    def handle(self, *args, **options):
        seeds = {}
        branches = {}
        leaves = {}
        
        apps = settings.INSTALLED_APPS
        for app in apps:
            app_seeds, app_branches, app_leaves = self.process_app(app)
            seeds.update(app_seeds)
            branches.update(app_branches)
            leaves.update(app_leaves)
        
        print >> sys.stderr, "Seeds: %s\n" % seeds.values()
        print >> sys.stderr, "Branches: %s\n" % branches.values()
        print >> sys.stderr, "Leaves: %s\n" % leaves.values()
        print >> sys.stderr, "---------------------"
        
        dirt = Dirt(seeds, branches)
        dirt.start_growing()
        sys.stdout.write("[")
        first = True
        for objects in dirt.harvest():
            if not first:
                sys.stdout.write(', ')
            sys.stdout.write(objects[1:-1])
            first = False
        sys.stdout.write("]")
        sys.stderr.write('\n')

    def process_app(self, app):
        # Attempt to import the app's seed module.
        try:
            # if app == 'geo':
            #     import pdb;pdb.set_trace()
            module = import_module('%s.%s' % (app, CONFIG_NAME))
            seeds = {}
            branches = {}
            leaves = {}
            real_clazzes = [clazz for clazz in dir(module) if not clazz.startswith ("__")]
            for name in real_clazzes:
                obj = getattr(module, name)
                if (obj != Seed) and issubclass(obj, Seed):
                    seeds[model_namespace(obj.model)] = obj
                elif (obj != Branch) and issubclass(obj, Branch):
                    branches[model_namespace(obj.model)] = obj
            return (seeds, branches, leaves)
        except ImportError:
            #print "No seed found for %s" % app
            return ([], [], [])

