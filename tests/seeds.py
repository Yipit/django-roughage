from roughage import Seed, Branch

from app.models import Book

class BookSeed(Seed):
    
    model = Book
    
    querysets = [
        Book.objects.filter(title="Book 1")
    ]

# class BookBranch(Branch):
#     
#     model = "app.book"
#     
#     def trim_app__author(self, queryset):
#         return queryset[:2]
