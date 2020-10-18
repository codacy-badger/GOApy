.PHONY: all

REGISTRY_HOST=docker.io
USERNAME=$(USER)
NAME=$(shell basename $(PWD))

RELEASE_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-release-support
IMAGE=$(shell tr '[:upper:]' '[:lower:]' <<< $(NAME))

VERSION=$(shell . $(RELEASE_SUPPORT) ; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); getTag)

SHELL=/bin/bash

PYTHON_VERSION=3.8.5
PYTHON_MINOR_VERSION=3.8

all: venv install-in-venv test

test: unittest test-coverage

req:
ifeq ($(shell which pyenv), "pyenv not found")
	@echo "Installing pyenv"
	curl https://pyenv.run | bash
endif
ifneq ($(shell python --version|cut -d" " -f2), ${PYTHON_VERSION})
	@echo "Installing Python version ${PYTHON_VERSION}"
	pyenv install ${PYTHON_VERSION}
endif
	pyenv local ${PYTHON_VERSION}
	pip install poetry virtualenv

patch:
	poetry version patch

minor:
	poetry version minor

major:
	poetry version major

version:
	poetry version

tag: TAG=$(shell . $(RELEASE_SUPPORT); getTag $(VERSION))
tag: check-status
	@. $(RELEASE_SUPPORT) ; ! tagExists $(TAG) || (echo "ERROR: tag $(TAG) for version $(VERSION) already tagged in git" >&2 && exit 1) ;
	@. $(RELEASE_SUPPORT) ; setRelease $(VERSION)
	git add .release
	git commit -m "bumped to version $(VERSION)" ;
	git tag $(TAG) ;
	@[ -n "$(shell git remote -v)" ] && git push --tags

check-status:
	@. $(RELEASE_SUPPORT) ; ! hasChanges || (echo "ERROR: there are still outstanding changes" >&2 && exit 1) ;

check-release: .release
	@. $(RELEASE_SUPPORT) ; tagExists $(TAG) || (echo "ERROR: version not yet tagged in git. make [minor,major,patch]-release." >&2 && exit 1) ;
	@. $(RELEASE_SUPPORT) ; ! differsFromRelease $(TAG) || (echo "ERROR: current directory differs from tagged $(TAG). make [minor,major,patch]-release." ; exit 1)

venv: req
	poetry install

install:
	python setup.py install

format: venv
	autopep8 --in-place --aggressive --aggressive --aggressive --recursive Goap/

install-in-venv: venv install
	python setup.py install

unittest: install-in-venv
	echo "Action Class Unittests"
	pytest -v tests/Action_test.py
	echo "Sensor Class Unittests"
	pytest -v tests/Sensor_test.py
	echo "Automaton Class Unittests"
	pytest -v tests/Automaton_test.py
	echo "Fullstack Unittests"
	pytest -v tests/Planner_test.py

install-coveralls: venv install-in-venv
	pip install coveralls

test-coverage: install-coveralls
	coverage run --source=Goap/ setup.py test

docker-build:
	docker build -t goapy:$(shell poetry version|cut -d" " -f2) .

clean-venv:
	rm -rf .venv/

clean-build:
	rm -rf build/ *.egg-info/

clean-all: clean-venv clean-build

clean: clean-all