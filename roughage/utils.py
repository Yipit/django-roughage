from django.db.models.loading import get_model

def get_model_from_key(key):
    app, model = key.split("__")
    return get_model(app, model)

def model_namespace(model_instance):
    return "%s__%s" % (model_instance._meta.app_label, model_instance._meta.module_name)

def queryset_namespace(queryset):
    return "%s__%s" % (queryset.model._meta.app_label, queryset.model._meta.module_name)

# from http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]