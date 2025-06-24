.PHONY: install
install:
	uv pip install -e ".[dev]"
	pre-commit install

.PHONY: migrations
migrations:
	uv run manage.py makemigrations $(ARGS)

.PHONY: migrate
migrate:
	uv run manage.py migrate

.PHONY: superuser
superuser:
	uv run manage.py createsuperuser

.PHONY: run
run:
	uv run manage.py runserver

.PHONY: run-cert
run-cert:
	uv run manage.py runserver_plus --cert-file cert.crt
	
.PHONY: clean
clean: 
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	find . -name ".pytest_cache" -delete
	find . -name ".coverage" -delete
	find . -name "htmlcov" -delete