## Creating a Testing and Virtual Environment
REQUIREMENTS:
- you need python3 to create a virtual environment

Steps:

(1) clone the repository into your local environment inside the 
directort structure `ansible_collections/ibm/power_aix
```
git clone https://github.com/IBM/ansible-power-aix.git ansible_collections/ibm/power_aix
```

(2) `cd ansible_collections/ibm/power_aix`

(3) create a virtual environment using the built-in `venv` module of `python3`
```
python3 -m venv <name_of_virtual_environment>
```
**NOTE**: This will create a directory named `<name_of_virtual_environment>` in the
current working directory. Make sure you DO NOT push this to your remote repository.

(4) activate virtual environment
```
source <name_of_virtual_environement>/bin/activate
```
**NOTE**: to deactivate virtual environment just run the command `deactivate` whilst
the virtual environment is active.

(5) install ansible 2.9 (if any issue, then install 2.10.7)
```
python -m pip install --upgrade pip
python -m pip install ansible==2.9.*
```
**NOTE**: You can also use the utility `Makefile` included in the repo by running
`make install-ansible ANSIBLE_VERSION=2.9`

(6) `export ANSIBLE_COLLECTIONS_PATHS=<path/to/ansible_collections>`

e.g. if `ansible_collections/ibm/power_aix` is in `$(HOME)/Ansible/ansible_collections/ibm/power_aix`
then run `export ANSIBLE_COLLECTIONS_PATHS=$(HOME)/Ansible`

--------------------------------------------------------------------------------------------------------
## Running Sanity Tests Locally
REQUIREMENTS:
- must use python **3.8**>=

Steps:

(1) setup testing and virtual environment

(2) install sanity test requirements
```
python -m pip install -r tests/sanity/sanity.requirements
```
**NOTE**: You can also run `make install-sanity-test-requirements`

(3) run the sanity test
```
ansible-test sanity -v --python 3.8 --exclude plugins/modules/_*.py plugins/modules/
```
**NOTE**: you can also just use `make sanity-test` instead

--------------------------------------------------------------------------------------------------------
## Running Unit Tests Locally
Steps:

(1) setup testing and virtual environment

(2) install unit test requirements
```
python -m pip install -r tests/unit/unit.requirements
```
**NOTE**: You can also run `make install-unit-test-requirements`

(3) run the sanity test
```
ansible-test units -v --python 3.8
```
**NOTE**: you can also just use `make unit-test` instead

--------------------------------------------------------------------------------------------------------
## Running PEP8 linting locally
Steps:

(1) follow **Running Sanity Tests Locally** up until step (2)

(2) run `make lint`

**NOTE**: 
if it does not work use
`flake8 plugins/modules/*.py --ignore=E402,W503 --max-line-length=160 --exclude=plugins/modules/_*.py` and
`python -m pycodestyle --ignore=E402,W503 --max-line-length=160 --exclude=plugins/modules/_*.py plugins/modules/*.py`
instead

--------------------------------------------------------------------------------------------------------
## Running compile test locally
**NOTE**: to make sure that the collection's modules are compatible with the
specified python version
Steps:

(1) follow **Running Sanity Tests Locally** up until step (2)

(2) run `make compile`

**NOTE**:
- to run on a specific python version `make compile PYTHON_VERSION=<*.* version>`
- if it does not work use `ansible-test sanity --test compile --python <*.* version> plugins/modules/*.py

--------------------------------------------------------------------------------------------------------
## CI Testing
- on pull request to `dev-collection` branch, the github actions workflow will trigger
sanity and unit testing.
- sanity testing will include PEP8 linting, compile testing, and ansible sanity test

--------------------------------------------------------------------------------------------------------
## Guidelines For Creating Unit Tests
- creating unit tests for `plugins/modules/<module_name>.py` must be written in the corresponding 
`tests/unit/plugins/modules/test_<module_name>.py` test module
- creating unit tests for `plugins/action/<module_name>.py` must be written in the corresponding 
`tests/unit/plugins/action/test_<module_name>.py` test module
- for mocking purposes we are using the built-in python module `unittest.mock`
- for running the test we use `ansible-test units` as a test runner
- (soft suggestion) when mocking, use a context manager method instead of decorators, etc.
- for common utility functions used in unit testings, add them to `tests/unit/plugins/modules/common/util.py`
- if you need files which contains text information needed for unit testing (such as mocking an expected text
output from a call), store them in `tests/unit/plugins/module/common`


--------------------------------------------------------------------------------------------------------
## Resources
- [unittest](https://docs.python.org/3.7/library/unittest.html) documentation
- [regular expressions](https://docs.python.org/3.7/library/re.html) documentation
- [ansible unit testing](https://docs.ansible.com/ansible/latest/dev_guide/testing_units.html) documentation
