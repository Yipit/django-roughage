
import os
import sys
import unittest

import StringIO

test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(test_dir, os.path.pardir))
os.environ["DJANGO_SETTINGS_MODULE"] = 'settings'


from django.test import simple
from django.core.management import call_command
from app.models import Book, Author, Publisher

class RoughageTestSuite(unittest.TestCase):
    def setUp(self):
        bob_johnson = Author.objects.create(first_name="Bob", last_name="Johnson")
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

        b6 = Book.objects.create(publisher=penguin, title="Ghost Protocol")

    def test_plant(self):
        stream = StringIO.StringIO()
        call_command('plant', stream=stream)
        stream.seek(0)
        print stream.read()
        

if __name__ == "__main__":
    runner = simple.DjangoTestSuiteRunner()
    try:
        old_config = runner.setup_databases()
        unittest.main()
    finally:
        runner.teardown_databases(old_config)