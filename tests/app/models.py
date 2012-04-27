from django.db import models


class Publisher(models.Model):
    
    name = models.CharField(max_length=255)


class Author(models.Model):
    
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)


class Book(models.Model):
    
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author)
    publisher = models.ForeignKey(Publisher)

