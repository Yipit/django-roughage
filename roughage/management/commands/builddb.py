import json

from collections import defaultdict
from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        call_command('syncdb')
        if 'south' in settings.INSTALLED_APPS:
            filename = args[0]
            data = json.load(open(filename, 'r'))
            migration_history = [obj for obj in data if obj['model'] == "south.migrationhistory"]
            migrations = defaultdict(SortedList)
            for migration in migration_history:
                app_name = migration['fields']['app_name']
                name = migration['fields']['migration']
                migrations[app_name].append(name)
            for app, migration_list in migrations.iteritems():
                if not app in settings.INSTALLED_APPS:
                    print "{} not in Installed APPS".format(app)
                    continue
                to = migration_list[-1]
                try:
                    call_command('migrate', app, to)
                except Exception:
                    pass



class SortedList(list):
    """
    Utility class for keeping migration_histories sorted
    """
    def append(self, obj):
        list.append(self, obj)
        self.sort()
