from roughage import Seed

from app.models import Author


class AuthorSeed(Seed):

    model = Author

    def querysets(self):
        return [
            Author.objects.all()
        ]
