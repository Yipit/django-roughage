from roughage import Seed, Branch

from app.models import Author

class AuthorSeed(Seed):
    
    model = Author
    
    querysets = [
        Author.objects.all()
    ]