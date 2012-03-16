import inspect
import sys

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import signals
from django.db.models.loading import get_models, get_apps
from django.dispatch.dispatcher import Signal
from django.utils.importlib import import_module
CONFIG_NAME = 'seeds'

from seed_app.bases import Branch, Seed, Dirt
from seed_app.utils import model_namespace

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        clazz_names = [clazz_name for clazz_name in dir(signals) if not clazz_name.startswith ("__")]
        clazzes = [getattr(signals, clazz_name) for clazz_name in clazz_names]
        all_signals =  [clazz for clazz in clazzes if isinstance(clazz, Signal)]
        for signal in all_signals:
            signal.receivers = []

        #~ Disable foreign key checks during fixture loading
        from django.db import connections, DEFAULT_DB_ALIAS
        connection = connections[DEFAULT_DB_ALIAS]
        if 'mysql' in connection.settings_dict['ENGINE']:
            cursor = connection.cursor()
            cursor.execute('SET foreign_key_checks = 0')

        #~ Load fixture
        from django.core.management import call_command
        call_command('loaddata', args[0], verbosity=0)

        #~ Enable foreign key checks after fixture loading
        if 'mysql' in connection.settings_dict['ENGINE']:
            cursor = connection.cursor()
            cursor.execute('SET foreign_key_checks = 1')
        connection.close()
