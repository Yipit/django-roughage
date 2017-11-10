import django

from django.apps import apps
from distutils.version import LooseVersion


def get_model_from_key(key):
    app, model = key.split("__")
    return apps.get_model(app, model)


def model_namespace(model_instance):
    return "%s__%s" % (model_instance._meta.app_label, model_instance._meta.model_name)


def queryset_namespace(queryset):
    return "%s__%s" % (queryset.model._meta.app_label, queryset.model._meta.module_name)


def get_all_related_objects(obj):
    all_related_objects = [
        field for field in obj._meta.get_fields()
        if (field.one_to_many or field.one_to_one)
        and field.auto_created and not field.concrete
    ]
    return all_related_objects


# from http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def is_django_version_greater_than(version):
    django_version = LooseVersion(django.get_version())
    return django_version >= version
