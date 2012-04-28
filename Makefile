init:
	pip install -r requirements.txt --use-mirrors

test:
	nosetests --nocapture tests