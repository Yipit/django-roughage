from roughage import Seed

from tests.app.models import Pseudonym


class BookSeed(Seed):

    model = Pseudonym

    def querysets(self):
        return [
            Pseudonym.objects.all()
        ]
