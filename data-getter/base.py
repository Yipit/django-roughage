from django.db.models.loading import get_model

class MetaClass(type):
    
    def __new__(cls, name, bases, attrs):
        app, model =  attrs.get('model').split(".")
        attrs['_model'] = get_model(app, model)
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)


        