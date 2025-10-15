install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e .

lint-fix:
	.venv/bin/black .

lint-check:
	.venv/bin/black --check .

test:
	.venv/bin/pytest

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .venv/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete