PYTHON_VERSION := $(shell python -c "import sys; print('%d.%d' % sys.version_info[0:2])")

.PHONY: help
help:
	@echo "usage: make <target>"
	@echo ""
	@echo "target:"
	@echo "clean					clean junk files"
	@echo "install-unit-test-requirements 		install python modules needed run unit testing"
	@echo "unit-test 				run unit test suite for the collection"

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
