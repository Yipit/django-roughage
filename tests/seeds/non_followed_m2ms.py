from roughage import Seed

from app.models import BookReport


class BookSeed(Seed):

    model = BookReport

    querysets = [
        BookReport.objects.filter(id=1)
    ]
