SHELL := /bin/bash
rwildcard=$(foreach d,$(wildcard $(1:=/*)),$(call rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))

PYEXECPATH ?= $(shell which python3.10 || which python3.11 || which python3.10 || which python3.9 || which python3.8 || which python3.7 || which python3)
PYTHON ?= $(shell basename $(PYEXECPATH))
VENV := .venv
SOURCE_VENV := source $(VENV)/bin/activate;
PYEXEC := $(SOURCE_VENV) python
INPUT_REQS := requirements.in
DEV_INPUT_REQS := requirements-dev.in
ALL_REQS := $(INPUT_REQS) $(DEV_INPUT_REQS) $(wildcard requirements-dev/*.in)
REQS_MARKER := $(VENV)/bin/.pip-sync


PIP := $(PYEXEC) -m pip
UV_PIP := $(SOURCE_VENV) uv pip
PIP_SYNC := $(UV_PIP) sync
PIP_COMPILE := $(UV_PIP) compile --no-header
TMPDIR ?= /tmp
TEMP_VENV := $(TMPDIR)/cruft-venv
CRUFT := source $(TEMP_VENV)/bin/activate; cruft
BUMPVERSION := source $(TEMP_VENV)/bin/activate; bumpversion
BASH := bash
setup := $(PYEXEC) setup.py

package_dir := mbd_core
tests_dir := tests
coverage_percent = 100
PYTEST_COMMAND := $(PYEXEC) -m pytest --cov=. --cov-fail-under=$(coverage_percent) --cov-config=pyproject.toml --cov-report=xml:coverage.xml --cov-report=term-missing --cov-branch $(package_dir) $(tests_dir)

$(ALL_REQS) &:
	@touch $(ALL_REQS)

$(REQS_MARKER): $(ALL_REQS)
	make resolve-requirements

.PHONY: init-venv
init-venv:
	$(PYTHON) -m venv $(VENV)
	@touch $(REQS_MARKER)

.PHONY: setup-uv
setup-uv:
	test -f $(VENV)/bin/activate || make init-venv
	$(PIP) install -U setuptools pip uv wheel
	@touch $(VENV)/bin/.uv_is_setup

.PHONY: uv
uv:
	test -f $(VENV)/bin/.uv_is_setup || make setup-uv

.PHONY: sync-dev-requirements
sync-dev-requirements: uv $(REQS_MARKER)
	test -f requirements-dev.txt || make resolve-requirements
	$(PIP_SYNC) requirements-dev.txt

.PHONY: resolve-requirements
resolve-requirements: export CUSTOM_COMPILE_COMMAND="make update-requirements"
resolve-requirements: uv
	$(PIP_COMPILE) --output-file=requirements-dev.txt $(DEV_INPUT_REQS)
	@echo "Updated requirements-dev.txt"
	$(PIP_COMPILE) --output-file=requirements.txt $(INPUT_REQS)
	@echo "Updated requirements.txt"
	@touch $(REQS_MARKER)

.PHONY: update-requirements
update-requirements: export CUSTOM_COMPILE_COMMAND="make update-requirements"
update-requirements: ## Update all requirements to latest versions.
update-requirements: uv
	$(PIP_COMPILE) --upgrade --output-file=requirements-dev.txt $(DEV_INPUT_REQS)
	@echo "Updated requirements-dev.txt"
	$(PIP_COMPILE) --upgrade --output-file=requirements.txt $(INPUT_REQS)
	@echo "Updated requirements.txt"
	@touch $(REQS_MARKER)
	make sync-dev-requirements

.PHONY: format-fix
format-fix: sync-dev-requirements
	$(PYEXEC) -m ruff format -q $(package_dir)
	$(PYEXEC) -m ruff format -q $(tests_dir)

.PHONY: ruff-fix
ruff-fix: sync-dev-requirements
	$(PYEXEC) -m ruff check --fix-only -e $(package_dir)
	$(PYEXEC) -m ruff check --fix-only -e $(tests_dir)

.PHONY: fix-lint
fix-lint: ## Auto-fix linting errors.
fix-lint: ruff-fix format-fix

.PHONY: format
format: sync-dev-requirements
	$(PYEXEC) -m ruff format --check $(package_dir)
	$(PYEXEC) -m ruff format --check $(tests_dir)

.PHONY: mypy
mypy: sync-dev-requirements
	$(PYEXEC) -m mypy --config-file pyproject.toml $(package_dir)

.PHONY: ruff
ruff: sync-dev-requirements
	$(PYEXEC) -m ruff check $(package_dir)
	$(PYEXEC) -m ruff check $(tests_dir)


.PHONY: blocklint
blocklint: sync-dev-requirements
	$(PYEXEC) -m blocklint --max-issue-threshold 1 $(package_dir)

.PHONY: yamllint
yamllint: sync-dev-requirements
	$(PYEXEC) -m yamllint -d "{extends: relaxed, rules: {line-length: {max: 88, allow-non-breakable-words: true}}, ignore-from-file: .gitignore}" ./

.PHONY: lint
lint: ## Run lint checks.
lint: ruff mypy format blocklint yamllint

.PHONY: test
test: ## Run all tests.
test: sync-dev-requirements
	$(PYTEST_COMMAND)

.PHONY: release-patch release-minor release-major
release-patch:
	bump2version patch

release-minor:
	bump2version minor

release-major:
	bump2version major

release-tag:
	git push
	git push --tags
