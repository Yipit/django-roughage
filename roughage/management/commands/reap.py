import json
from collections import defaultdict

from django.apps import apps
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.management import create_contenttypes
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.db.models import signals
from django.dispatch.dispatcher import Signal


class Command(LoadDataCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-d",
            "--no-signals",
            dest="use_signals",
            default=True,
            help='Disconnects all signals during import',
            action="store_false"
        )

    def process_migrations(self, data):

        class SortedList(list):
            """
            Utility class for keeping migration_histories sorted
            """
            def append(self, obj):
                list.append(self, obj)
                self.sort()

        migration_history = [obj for obj in data if obj['model'] == "south.migrationhistory"]
        migration_lists = defaultdict(SortedList)
        migrations = {}
        for migration in migration_history:
            app_name = migration['fields']['app_name']
            name = migration['fields']['migration']
            migration_lists[app_name].append(name)
        for app, migration_list in migration_lists.iteritems():
            if not app in settings.INSTALLED_APPS:
                print "{} not in Installed APPS".format(app)
                continue
            to = migration_list[-1]
            migrations[app] = to
        return migrations

    def disable_signals(self):
        clazz_names = [clazz_name for clazz_name in dir(signals) if not clazz_name.startswith("__")]
        clazzes = [getattr(signals, clazz_name) for clazz_name in clazz_names]
        all_signals = [clazz for clazz in clazzes if isinstance(clazz, Signal)]
        for signal in all_signals:
            signal.receivers = []

    def _update_contenttypes(self, *args, **kwargs):
        for app_config in apps.get_app_configs():
            create_contenttypes(app_config)

    def handle(self, *args, **options):
        signals.post_migrate.disconnect(self._update_contenttypes)
        signals.post_migrate.disconnect(create_permissions, dispatch_uid="django.contrib.auth.management.create_permissions")
        migrate_kwargs = {'ignore': True}
        if 'settings' in options:
            migrate_kwargs['settings'] = options.get('settings')
        call_command('migrate', interactive=False, **migrate_kwargs)

        if 'south' in settings.INSTALLED_APPS:
            filename = args[0]
            data = json.load(open(filename, 'r'))
            migrations = self.process_migrations(data)
            for app, to in migrations.iteritems():
                try:
                    call_command('migrate', app, to)
                except Exception:
                    pass
            import django.core.serializers.python
            orig_get_model = django.core.serializers.python._get_model

            def _get_model(model_indentifier):
                from south.migration.base import Migrations
                app, model = model_indentifier.split(".")
                if app in migrations:
                    latest = migrations[app]
                    orm = Migrations(app).migration(latest).orm()
                    return orm[model_indentifier]
                else:
                    return orig_get_model(model_indentifier)

            django.core.serializers.python._get_model = _get_model

        if not options.pop('use_signals'):
            self.disable_signals()

        # Delete all content types that were created whil migrating. They will get recreated post loaddate
        ContentType.objects.all().delete()

        super(Command, self).handle(*args, **options)

        signals.post_migrate.connect(self._update_contenttypes)
        signals.post_migrate.connect(create_permissions, dispatch_uid="django.contrib.auth.management.create_permissions")
        call_command('migrate')

        # if 'south' in settings.INSTALLED_APPS:
        #     call_command('migrate')
