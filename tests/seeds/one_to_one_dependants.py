from roughage import Seed

from app.models import Author


class AuthorSeed(Seed):

    model = Author

    querysets = [
        Author.objects.all()
    ]
