def queryset_namespace(queryset):
    return "%s.%s" % (queryset.model._meta.app_label, queryset.model._meta.module_name)
