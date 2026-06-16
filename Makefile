ifndef PYTHON_VERSION
	PYTHON_VERSION := $(shell python3 -c "import sys; print('%d.%d' % sys.version_info[0:2])")
endif

ifndef MODULE
	MODULE = plugins/modules/*.py plugins/action/*.py
endif

ifndef EDA_MODULE
	EDA_MODULE = extensions/eda/plugins/event_source/*.py
endif

ifndef ROLE
	ROLE = roles
endif

ifndef PLAYBOOK
	PLAYBOOK = playbooks
endif

ifndef SHELLSCRIPT
	SHELLSCRIPT := $(shell find roles -name "*.sh")
endif

VIOSHC_SCRIPT = roles/power_aix_vioshc/files/vioshc.py

ifndef TEST
	TEST = tests/unit/plugins/modules/*.py
endif

DEPRECATED = plugins/modules/_*.py
TEST_OMIT = $(DEPRECATED),tests/*

######################################################################################
# utility targets
######################################################################################

.PHONY: help
help:
	@echo "usage: make <target>"
	@echo ""
	@echo "target:"
	@echo "install-requirements ANSIBLE_VERSION=<version> 	install all requirements"
	@echo "install-ansible ANSIBLE_VERSION=<version>	install ansible: 2.9, 3, or 4"
	@echo "install-ansible-devel-branch			install ansible development branch"
	@echo "install-sanity-test-requirements		install python modules needed to \
	run sanity testing"
	@echo "install-unit-test-requirements 			install python modules needed \
	run unit testing"
	@echo "lint 						lint ansible modules, EDA plugins, playbooks, and roles"
	@echo "module-lint MODULE=<module path> 		lint ansible module"
	@echo "eda-lint EDA_MODULE=<eda module path> 		lint EDA event source plugins and playbooks"
	@echo "playbook-lint PLAYBOOK=<playbook path> 		lint ansible playbooks"
	@echo "role-lint ROLE=<role path> 			lint ansible role"
	@echo "porting MODULE=<module path>			check if module is python3 ported"
	@echo "sanity-test MODULE=<module path>		run sanity test on the collections"
	@echo "unit-test TEST=<test path>			run unit test suite for the collection"
	@echo "clean						clean junk files"

.PHONY: clean
clean:
	@rm -rf tests/unit/plugins/modules/__pycache__
	@rm -rf tests/unit/plugins/modules/common/__pycache__
	@rm -rf collections/ansible_collections
	@rm -rf plugins/modules/__pycache__

.PHONY: uninstall-pylint
uninstall-pylint:
	python -m pip uninstall --yes pylint

######################################################################################
# installation targets
######################################################################################

.PHONY: install-requirements
install-requirements: install-ansible install-sanity-test-requirements \
		install-unit-test-requirements
	python3 -m pip install --upgrade pip

.PHONY: install-ansible
install-ansible:
	python3 -m pip install --upgrade pip
ifdef ANSIBLE_VERSION
	python3 -m pip install ansible==$(ANSIBLE_VERSION).*
else
	python3 -m pip install ansible
endif

.PHONY: install-ansible-devel-branch
install-ansible-devel-branch:
	python3 -m pip install --upgrade pip
	python3 -m pip install https://github.com/ansible/ansible/archive/devel.tar.gz \
	--disable-pip-version-check

.PHONY: install-sanity-test-requirements
install-sanity-test-requirements:
	python3 -m pip install -r tests/sanity/sanity.requirements

.PHONY: install-unit-test-requirements
install-unit-test-requirements:
	python3 -m pip install -r tests/unit/unit.requirements

.PHONY: install-pylint-py3k
install-pylint-py3k: uninstall-pylint
	python3 -m pip install --upgrade pip
	python3 -m pip install pylint==2.10.*

######################################################################################
# testing targets
######################################################################################

.PHONY: lint
lint: module-lint eda-lint playbook-lint role-lint

.PHONY: module-lint
module-lint:
	ansible-test sanity -v --color yes --truncate 0 --python $(PYTHON_VERSION) \
 	--exclude $(DEPRECATED) --test pylint $(MODULE)
	ansible-test sanity -v --color yes --truncate 0 --python $(PYTHON_VERSION) \
 	--exclude $(DEPRECATED) --test yamllint $(MODULE)
	flake8 --ignore=E402,W503 --max-line-length=160 --exclude $(DEPRECATED) $(MODULE)
	python3 -m pycodestyle --ignore=E402,W503 --max-line-length=160 --exclude $(DEPRECATED) \
		$(MODULE)

.PHONY: eda-lint
eda-lint:
	@echo "Running EDA plugin linting..."
	@echo "Running ruff..."
	ruff check --select ALL --ignore D100,D104,INP001,FA102,UP001,UP010,I001,FA100,PLR0913,E501 $(EDA_MODULE)
	@echo "Running flake8..."
	flake8 --ignore=E402,W503 --max-line-length=160 $(EDA_MODULE)
	@echo "Running pycodestyle..."
	python3 -m pycodestyle --ignore=E402,W503 --max-line-length=160 $(EDA_MODULE)
	@echo "Running pylint..."
	pylint --max-line-length=160 --disable=C0103,C0114,C0115,C0116,R0913,R0914,W0703 $(EDA_MODULE)
	@echo "Checking EDA YAML files (plugins and playbooks)..."
	@if [ -n "$$(find extensions/eda playbooks/eda -name '*.yml' -o -name '*.yaml' 2>/dev/null)" ]; then \
		yamllint -d "{extends: default, rules: {line-length: {max: 160}, comments: {min-spaces-from-content: 1}, trailing-spaces: enable}}" \
		$$(find extensions/eda playbooks/eda -name '*.yml' -o -name '*.yaml' 2>/dev/null); \
	else \
		echo "No YAML files found in EDA directories"; \
	fi
	@echo "Running ansible-lint on EDA playbooks..."
	@if [ -d "playbooks/eda" ]; then \
		ansible-lint --force-color --strict playbooks/eda/; \
	fi

.PHONY: playbook-lint
playbook-lint:
	@echo "Running playbook linting..."
	@echo "Running yamllint on playbooks (excluding EDA)..."
	@if [ -n "$$(find $(PLAYBOOK) -maxdepth 1 -name '*.yml' -o -name '*.yaml' 2>/dev/null)" ]; then \
		yamllint -s -d "{extends: default, rules: {line-length: {max: 160}, comments: {min-spaces-from-content: 1}, trailing-spaces: enable}}" \
		$$(find $(PLAYBOOK) -maxdepth 1 -name '*.yml' -o -name '*.yaml' 2>/dev/null); \
	else \
		echo "No YAML files found in playbooks directory"; \
	fi
	@echo "Running ansible-lint on playbooks (excluding EDA)..."
	@if [ -n "$$(find $(PLAYBOOK) -maxdepth 1 -name '*.yml' -o -name '*.yaml' 2>/dev/null)" ]; then \
		ansible-lint --force-color $$(find $(PLAYBOOK) -maxdepth 1 -name '*.yml' -o -name '*.yaml' 2>/dev/null); \
	fi

.PHONY: role-lint
role-lint:
	ansible-lint --force-color -f pep8 $(ROLE)

.PHONY: porting
porting:
	python3 -m pylint --py3k --output-format=colorized $(MODULE) $(VIOSHC_SCRIPT)

.PHONY: compile
compile:
	ansible-test sanity --test compile --python $(PYTHON_VERSION) $(MODULE)

.PHONY: sanity-test
sanity-test:
	ansible-test sanity -v --color yes --truncate 0 --python $(PYTHON_VERSION) \
		--exclude $(DEPRECATED) $(MODULE)

.PHONY: unit-test
unit-test:
	@if [ -d "tests/output/coverage" ]; then \
		ansible-test coverage erase; \
	fi
	ansible-test units -v --color yes --python $(PYTHON_VERSION) \
	--coverage $(TEST)
	
	@if [ -d "tests/output/coverage" ] && [ -n "$$(find tests/output/coverage -name '.coverage*' 2>/dev/null)" ]; then \
		ansible-test coverage report --omit $(TEST_OMIT) --include "$(MODULE)" --show-missing; \
	else \
		echo "No coverage data found, skipping coverage report"; \
	fi
