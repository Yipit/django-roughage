from roughage import Seed

from app.models import Book


class BookSeed(Seed):

    model = Book

    def querysets(self):
        return [
            Book.objects.filter(id=1)
        ]
