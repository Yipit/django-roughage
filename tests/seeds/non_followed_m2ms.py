from roughage import Seed

from app.models import BookReport


class BookSeed(Seed):

    model = BookReport

    def querysets(self):
        return [
            BookReport.objects.filter(id=1)
        ]
