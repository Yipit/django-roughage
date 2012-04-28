from roughage import Seed

from app.models import Pseudonym

class BookSeed(Seed):
    
    model = Pseudonym
    
    querysets = [
        Pseudonym.objects.all()
    ]