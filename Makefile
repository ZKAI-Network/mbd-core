# Load environment variables from .env if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip build twine
	.venv/bin/pip install -e .

lint-fix:
	.venv/bin/black .

lint-check:
	.venv/bin/black --check .

lint:
	$(MAKE) install
	$(MAKE) lint-check

test:
	echo "No tests yet"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .venv/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	.venv/bin/python -m build

check-dist:
	.venv/bin/twine check dist/*

publish-test:
	@if [ -z "$$PYPI_API_TOKEN_TEST" ]; then echo "Error: PYPI_API_TOKEN_TEST not set"; exit 1; fi
	.venv/bin/twine upload --repository-url https://test.pypi.org/legacy/ -u __token__ -p "$$PYPI_API_TOKEN_TEST" dist/*

publish:
	@if [ -z "$$PYPI_API_TOKEN_PROD" ]; then echo "Error: PYPI_API_TOKEN_PROD not set"; exit 1; fi
	.venv/bin/twine upload -u __token__ -p "$$PYPI_API_TOKEN_PROD" dist/*
