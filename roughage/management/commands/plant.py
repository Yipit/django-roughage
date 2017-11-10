import inspect
import sys
from importlib import import_module

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
CONFIG_NAME = 'seeds'

from roughage.base import Seed, Dirt
from roughage.utils import model_namespace


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--database",
            dest="database",
            default="default",
            help='The database name to pull data from'
        )
        parser.add_argument(
            "-f",
            "--file",
            dest="dest_file",
            default=None,
            help='The filename to put data in'
        )
        parser.add_argument(
            "-s",
            "--seeds",
            dest="seeds_module",
            default='seeds',
            help='The seeds module'
        )

    def handle(self, *args, **options):
        self.seeds = {}
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
            print >> sys.stderr, "Now Growing..."

        dirt = Dirt(self.database, self.seeds)
        dirt.start_growing()
        dirt.print_soil(verbosity)
        dirt.harvest(stream)

    def get_stream(self, options):

        # command was called programatically.
        # return the stream the was passed in
        if options.get('stream'):
            return options.get('stream')

        dest_file = options.get('dest_file')
        if dest_file:
            return open(dest_file, 'w')

        else:
            return sys.stdout

    def process_module(self, module):
        seeds = {}
        real_clazzes = [clazz for clazz in dir(module) if not clazz.startswith("__")]
        for name in real_clazzes:
            obj = getattr(module, name)
            if inspect.isclass(obj) and (obj != Seed) and issubclass(obj, Seed):
                seeds[model_namespace(obj.model)] = obj
        self.seeds.update(seeds)

    def process_app(self, app):
        # Attempt to import the app's seed module.
        try:
            module = import_module('%s.%s' % (app, CONFIG_NAME))
        except ImportError:
            pass
        else:
            self.process_module(module)
