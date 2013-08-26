from roughage import Seed

from app.models import Book, BookReport


class BookSeed(Seed):

    model = Book

    def querysets(self):
        return [
            Book.objects.filter(pk__lt=3)
        ]


class BookReportSeed(Seed):

    model = BookReport

    def trim_app__book(self, queryset):
        return queryset[:2]
