from roughage import Seed

from app.models import Book, BookReport


class BookSeed(Seed):

    model = Book

    querysets = [
        Book.objects.filter(id__lt=3)
    ]


class BookReportSeed(Seed):

    model = BookReport

    def trim_app__book(self, queryset):
        return queryset[:2]
