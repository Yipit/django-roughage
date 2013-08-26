import os
import sys
import unittest
import json
import StringIO

test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(test_dir, os.path.pardir))
os.environ["DJANGO_SETTINGS_MODULE"] = 'settings'

from django.test import simple
from django.core.management import call_command
from app.models import Book, Author, Publisher, BookReport, Pseudonym
from sure import that
from roughage.base import SOIL

"""
Things test data should confirm:

Objects with FK dependencies get the dependencies
Objects with Non-followed M2Ms get the ungotten objects stripped
Objects with followed M2Ms get the objects
Objects with OneToOne dependencies get the dependencies
Objects with OneToOne dependencies are added when the dependencies are added

"""


class RoughageTestSuiteBase(object):

    def setUp(self):
        self.runner = simple.DjangoTestSuiteRunner()
        self.old_config = self.runner.setup_databases()
        self.create_data()
        SOIL.reset()

    def tearDown(self):
        self.runner.teardown_databases(self.old_config)

    def create_data(self):
        bob_johnson = Author.objects.create(first_name="Bob", last_name="Johnson", pk=1)
        bob_thorton = Author.objects.create(first_name="Bob", last_name="Thorton")
        george_costanza = Author.objects.create(first_name="George", last_name="Costanza")

        random_house = Publisher.objects.create(name="Random House")
        penguin = Publisher.objects.create(name="Penguin")

        b1 = Book.objects.create(publisher=random_house, title="Book 1")
        b1.authors.add(bob_johnson, bob_thorton)

        b2 = Book.objects.create(publisher=random_house, title="Book 2")
        b2.authors.add(bob_johnson, george_costanza)

        b3 = Book.objects.create(publisher=random_house, title="Book 3")
        b3.authors.add(george_costanza)

        b4 = Book.objects.create(publisher=penguin, title="Book 4")
        b4.authors.add(bob_thorton, george_costanza)

        b5 = Book.objects.create(publisher=penguin, title="Book 5")
        b5.authors.add(bob_johnson, bob_thorton, george_costanza)

        Book.objects.create(publisher=penguin, title="Ghost Protocol")

    def test_plant(self):
        stream = StringIO.StringIO()
        call_command('plant', stream=stream, seeds_module=self.seeds_module)
        stream.seek(0)
        actual_json = stream.read()
        print actual_json

        assert that(json.loads(actual_json)).equals(self.expected)


class OneToOneDependants(RoughageTestSuiteBase, unittest.TestCase):

    def create_data(self):
        Author.objects.create(first_name="Bob", last_name="Johnson")
        bob_thorton = Author.objects.create(first_name="Bob", last_name="Thorton")
        Pseudonym.objects.create(author=bob_thorton, name="Janky Joe")

    seeds_module = 'seeds.one_to_one_dependants'
    expected = [
      {
        "pk": 1,
        "model": "app.pseudonym",
        "fields": {
          "name": "Janky Joe",
          "author": 2
        }
      },
      {
        "pk": 1,
        "model": "app.author",
        "fields": {
          "first_name": "Bob",
          "last_name": "Johnson"
        }
      },
      {
        "pk": 2,
        "model": "app.author",
        "fields": {
          "first_name": "Bob",
          "last_name": "Thorton"
        }
      },
    ]


class OneToOneDependencies(RoughageTestSuiteBase, unittest.TestCase):

    def create_data(self):
        Author.objects.create(first_name="Bob", last_name="Johnson")
        bob_thorton = Author.objects.create(first_name="Bob", last_name="Thorton")

        Pseudonym.objects.create(author=bob_thorton, name="Janky Joe")

    seeds_module = 'seeds.one_to_one_dependencies'
    expected = [
      {
        "pk": 1,
        "model": "app.pseudonym",
        "fields": {
          "name": "Janky Joe",
          "author": 2
        }
      },
      {
        "pk": 2,
        "model": "app.author",
        "fields": {
          "first_name": "Bob",
          "last_name": "Thorton"
        }
      }
    ]


class NonFollowedM2M(RoughageTestSuiteBase, unittest.TestCase):

    def create_data(self):
        bob_johnson = Author.objects.create(first_name="Bob", last_name="Johnson")
        bob_thorton = Author.objects.create(first_name="Bob", last_name="Thorton")

        random_house = Publisher.objects.create(name="Random House")
        Publisher.objects.create(name="Penguin")

        b1 = Book.objects.create(publisher=random_house, title="Book 1")
        b1.authors.add(bob_johnson, bob_thorton)

        BookReport.objects.create(grade=100, book=b1)

    seeds_module = 'seeds.non_followed_m2ms'
    expected = [
      {
        "pk": 1,
        "model": "app.publisher",
        "fields": {
          "name": "Random House"
        }
      },
      {
        "pk": 1,
        "model": "app.bookreport",
        "fields": {
          "grade": 100,
          "book": 1
        }
      },
      {
        "pk": 1,
        "model": "app.book",
        "fields": {
          "publisher": 1,
          "authors": [],
          "title": "Book 1"
        }
      },
    ]


class FollowedM2Ms(RoughageTestSuiteBase, unittest.TestCase):

    seeds_module = 'seeds.followed_m2ms'
    expected = [
      {
        "pk": 1,
        "model": "app.author",
        "fields": {
          "first_name": "Bob",
          "last_name": "Johnson"
        }
      },
      {
        "pk": 2,
        "model": "app.author",
        "fields": {
          "first_name": "Bob",
          "last_name": "Thorton"
        }
      },
      {
        "pk": 1,
        "model": "app.book",
        "fields": {
          "publisher": 1,
          "authors": [
            1,
            2
          ],
          "title": "Book 1"
        }
      },
      {
        "pk": 1,
        "model": "app.publisher",
        "fields": {
          "name": "Random House"
        }
      }
    ]


class GetForeignKeys(RoughageTestSuiteBase, unittest.TestCase):

    def create_data(self):
        penguin = Publisher.objects.create(name="Penguin")
        random_house = Publisher.objects.create(name="Random House")
        Author.objects.create(first_name="George", last_name="Costanza")

        Book.objects.create(publisher=penguin, title="Book 1", pk=1)
        Book.objects.create(publisher=random_house, title="Book 2")

    seeds_module = 'seeds.fk_dependencies'
    expected = [
      {
        "pk": 1,
        "model": "app.book",
        "fields": {
          "publisher": 1,
          "authors": [],
          "title": "Book 1"
        }
      },
      {
        "pk": 1,
        "model": "app.publisher",
        "fields": {
          "name": "Penguin"
        }
      }
    ]


class TrimM2M(RoughageTestSuiteBase, unittest.TestCase):
    def create_data(self):
        random_house = Publisher.objects.create(name="Random House")

        b1 = Book.objects.create(publisher=random_house, title="Book 1")
        b2 = Book.objects.create(publisher=random_house, title="Book 2")
        b3 = Book.objects.create(publisher=random_house, title="Book 3")
        BookReport.objects.create(grade=5, book=b1)
        BookReport.objects.create(grade=10, book=b1)
        BookReport.objects.create(grade=11, book=b1)
        BookReport.objects.create(grade=100, book=b2)
        BookReport.objects.create(grade=100, book=b3)

    seeds_module = 'seeds.basic_branch'
    expected = [
      {
        "pk": 1,
        "model": "app.bookreport",
        "fields": {
          "grade": 5,
          "book": 1
        }
      },
      {
        "pk": 2,
        "model": "app.bookreport",
        "fields": {
          "grade": 10,
          "book": 1
        }
      },
      {
        "pk": 4,
        "model": "app.bookreport",
        "fields": {
          "grade": 100,
          "book": 2
        }
      },
      {
        "pk": 1,
        "model": "app.book",
        "fields": {
          "publisher": 1,
          "authors": [],
          "title": "Book 1"
        }
      },
      {
        "pk": 2,
        "model": "app.book",
        "fields": {
          "publisher": 1,
          "authors": [],
          "title": "Book 2"
        }
      },
      {
        "pk": 1,
        "model": "app.publisher",
        "fields": {
          "name": "Random House"
        }
      }
    ]


if __name__ == "__main__":
    unittest.main()
