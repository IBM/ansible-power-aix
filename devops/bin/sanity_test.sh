#!/bin/bash

echo "======== $0 ========"
set -x
set -e
set -o pipefail
set -o errtrace

OUTPUTDIR=./documentation

err_report() {
    echo "Error running '$1' [rc=$2] line $3 "
}

trap 'err_report "$BASH_COMMAND" $? $LINENO' ERR

DIR="$(pwd)"

# build the virtual environment to run ansible-test
cd $ANSIBLE_DIR
git clone https://github.com/ansible/ansible.git
cd ansible
ANSIBLE_DIR="$(pwd)"

python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
. hacking/env-setup
pip install -r docs/docsite/requirements.txt
[[ -e $(find test/ -name sanity.txt) ]] && pip install -r $(find test/ -name sanity.txt)

# place the modules in the appropriate folder
cp $DIR/plugins/modules/*.py $ANSIBLE_DIR/lib/ansible/modules/

set +e

rc=0
for f in $DIR/plugins/modules/*.py; do
    f="${f##*/}"
    echo "-------- compile for $f --------"
    ansible-test sanity --test compile ${f%%.py} --python 2.7
    rc=$(($rc + $?))
    ansible-test sanity --test compile ${f%%.py} --python 3.7
    rc=$(($rc + $?))

    echo "-------- validate-modules for $f --------"
    ansible-test sanity --test validate-modules ${f%%.py}
    rc=$(($rc + $?))

done


set -e

deactivate

exit $rc
