def queryset_namespace(queryset):
    return "%s.%s" % (queryset.model._meta.app_label, queryset.model._meta.module_name)

# from http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]