setup:
	pip install -r development.txt --use-mirrors

test:
	nosetests tests
