.PHONY: install
install:
	uv pip install -e ".[dev]"

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
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

.PHONY: test
test:
	uv run pytest

.PHONY: format
format:
	uv tool run isort .
	uv tool run ruff format .