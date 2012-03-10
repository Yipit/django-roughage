def model_namespace(model_instance):
    return "%s__%s" % (model_instance._meta.app_label, model_instance._meta.module_name)

def queryset_namespace(queryset):
    return "%s__%s" % (queryset.model._meta.app_label, queryset.model._meta.module_name)
