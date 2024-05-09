SHELL=/bin/bash

PACKAGE-NAME=oldabe
DOCS-PATH=docs

export PYTEST_DISABLE_PLUGIN_AUTOLOAD = 1
UNIT_TESTS_PATH = tests/unit

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "install - install package and dependencies globally but from the local path"
	@echo "build - install package and dependencies for local development"
	@echo "install-docs - Install dependencies for building the documentation"
	@echo "build-docs - Build self-contained docs that could be hosted somewhere"
	@echo "docs - view docs in a browser"
	@echo "clean - clean all build and test artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint-source - check style for source with flake8"
	@echo "lint-tests - check style for tests with flake8"
	@echo "lint-all - check style with flake8"
	@echo "lint - alias for lint-source"
	@echo "black - run black auto-formatting on all code"
	@echo "test-unit - run unit tests"
	@echo "test - run specified tests, e.g.:"
	@echo "       make test DEST=tests/unit/my_module.py"
	@echo "       (defaults to unit tests if none specified)"
	@echo "test-stop - run tests and stop on the first failure"
	@echo "test-debug - run specified tests and enter debugger on the first failure. e.g."
	@echo "             make test-debug DEST=tests/unit/my_module.py"
	@echo "             (defaults to unit tests if none specified)"
	@echo "test-matrix - run tests on every Python version with tox"
	@echo "test-tldr - run specified tests and output just the stacktrace, e.g."
	@echo "             make test-tldr DEST=tests/unit/my_module.py"
	@echo "             (defaults to unit tests if none specified)"
	@echo "debug - alias for test-debug"
	@echo "tldr - alias for test-tldr"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "sdist - package"

install:
	pip install -e .

build:
	pip install -e .[dev]

build-for-test:
	pip install -e .[test]

install-docs:
	raco pkg install --deps search-auto --link $(PWD)/docs

build-docs:
	scribble ++style $(DOCS-PATH)/oldabe.css --htmls --dest $(DOCS-PATH) --dest-name output $(DOCS-PATH)/oldabe.scrbl

docs: build-docs
	open docs/output/index.html

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr pip-wheel-metadata/
	rm -fr .eggs/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr coverage_html_report/

lint-source:
	flake8 $(PACKAGE-NAME)

lint-tests:
	flake8 tests

lint-all: lint-source lint-tests

lint: lint-source

black:
	black $(PACKAGE-NAME) tests

test-unit:
	python setup.py test --addopts $(UNIT_TESTS_PATH)

test-all: clean-test test-unit

test:
ifdef DEST
	$(eval OPTS := --addopts $(DEST))
else
	$(eval OPTS := --addopts $(UNIT_TESTS_PATH))
endif
	python setup.py test $(OPTS)

# stop on first failing test
test-stop:
	python setup.py test --addopts -x

# debug on first failing test
test-debug:
ifdef DEST
	$(eval OPTS := --addopts "-x --pudb $(DEST)")
else
	$(eval OPTS := --addopts "-x --pudb $(UNIT_TESTS_PATH)")
endif
	python setup.py test $(OPTS)

test-matrix:
	tox

test-tldr:
ifdef DEST
	$(eval OPTS := --addopts "-p tldr -p no:sugar $(DEST)")
else
	$(eval OPTS := --addopts "-p tldr -p no:sugar $(UNIT_TESTS_PATH)")
endif
	python setup.py test $(OPTS)

# ideally this should launch pudb to step through the specified tests
debug: test-debug

tldr: test-tldr

coverage: clean-test
	coverage run --source $(PACKAGE-NAME) setup.py test --addopts $(UNIT_TESTS_PATH)
	coverage report -m
	coverage html
	open coverage_html_report/index.html

cover-coveralls: clean-test
	coverage run --source $(PACKAGE-NAME) setup.py test --addopts $(UNIT_TESTS_PATH)
	coveralls

sdist: clean
	python setup.py sdist
	ls -l dist

.PHONY: help build build-for-test docs clean clean-build clean-pyc clean-test lint-source lint-tests lint-all lint black test-unit test-all test test-stop test-debug test-matrix test-tldr test-wiki debug coverage cover-coveralls sdist
