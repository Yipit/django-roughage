# django-roughage
> Version 0.0.2

# What

It's an utility for fetching small subsets of data from your production servers to the local environment.

# installing

## first of all

    pip install django-roughage

## add it to your django project

on settings.py

```python
INSTALLED_APPS = (
    ...
    'roughage',
    ...
)

```

# reaping

    python manage.py reap

# planting

    python manage.py plant
