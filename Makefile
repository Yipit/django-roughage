setup:
	pip install -r development.txt

test:
	DJANGO_SETTINGS_MODULE=tests.settings django-admin test --verbosity 2
