from roughage import Seed, Branch

from app.models import Book

class BookSeed(Seed):
    
    model = Book
    
    querysets = [
        Book.objects.filter(id=1)
    ]