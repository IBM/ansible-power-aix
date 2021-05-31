PYTHON_VERSION := $(shell python -c "import sys; print('%d.%d' % sys.version_info[0:2])")

.PHONY: help
help:
	@echo "usage: make <target>"
	@echo ""
	@echo "target:"
	@echo "clean					clean junk files"
	@echo "lint					lint module"         
	@echo "install-unit-test-requirements 		install python modules needed run unit testing"
	@echo "unit-test 				run unit test suite for the collection"

.PHONY: lint
lint:
ifdef MODULE
	flake8 $(MODULE) --max-line-length=160 --ignore=E402,W503
	python -m pycodestyle --max-line-length=160 --ignore=E402,W503 $(MODULE)
	ansible-test sanity --test pep8 "$(MODULE)"
else
	flake8 plugins/modules/* --max-line-length=160 --ignore=E402,W503
	python -m pycodestyle --max-line-length=160 --ignore=E402,W503 plugins/modules/*
	ansible-test sanity --test pep8 "plugins/modules/*"
endif

.PHONY: install-unit-test-requirements
install-unit-test-requirements:
	python -m pip install -r tests/unit/unit.requirements

.PHONY: unit-test
unit-test:
	@if [ -d "tests/output/coverage" ]; then \
		ansible-test coverage erase; \
	fi
	ansible-test units -v --python $(PYTHON_VERSION)  --coverage
	ansible-test coverage report --include 'plugins/modules/*' --show-missing

.PHONY: clean
clean:
	@rm -rf tests/output
	@rm -rf tests/unit/plugins/modules/__pycache__
	@rm -rf tests/unit/plugins/modules/common/__pycache__
