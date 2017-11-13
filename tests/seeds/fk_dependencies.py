from roughage import Seed

from tests.app.models import Book


class BookSeed(Seed):

    model = Book

    def querysets(self):
        return [
            Book.objects.filter(pk=1)
        ]
