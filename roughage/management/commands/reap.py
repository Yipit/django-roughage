from optparse import make_option

from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.db.models import signals
from django.dispatch.dispatcher import Signal

class Command(LoadDataCommand):
    
    option_list = BaseCommand.option_list + (
        make_option("-d", "--no-signals", dest="use_signals", default=True, 
            help='Disconnects all signals during import', action="store_false"),
    )
    
    def disable_signals(self):
        clazz_names = [clazz_name for clazz_name in dir(signals) if not clazz_name.startswith ("__")]
        clazzes = [getattr(signals, clazz_name) for clazz_name in clazz_names]
        all_signals =  [clazz for clazz in clazzes if isinstance(clazz, Signal)]
        for signal in all_signals:
            signal.receivers = []
    
    def handle(self, *args, **options):
        if not options.pop('use_signals'):
            self.disable_signals()
        return super(Command, self).handle(*args, **options)
