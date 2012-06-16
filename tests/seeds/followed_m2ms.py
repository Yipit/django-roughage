from roughage import Seed

from app.models import Book


class BookSeed(Seed):

    model = Book

    querysets = [
        Book.objects.filter(id=1)
    ]
