#!/bin/bash

echo "======== $0 ========"
set -x
set -e
set -o pipefail
set -o errtrace

OUTPUTDIR=./documentation
PY_VERSIONS="2.7 3.7"

err_report() {
    echo "Error running '$1' [rc=$2] line $3 "
}

trap 'err_report "$BASH_COMMAND" $? $LINENO' ERR

DIR="$(pwd)"

# build the virtual environment to run ansible-test
cd
git clone https://github.com/ansible/ansible.git
cd ansible
ANSIBLE_DIR="$(pwd)"
SANITY_IGNORE="$ANSIBLE_DIR/test/sanity/ignore.txt"

python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
# skip the conflict checks but may require to manually resolve any issues afterwards
export ANSIBLE_SKIP_CONFLICT_CHECK=1
. hacking/env-setup
pip install -r docs/docsite/requirements.txt
pip install pylint yamllint pyyaml
pip3 install pyyaml voluptuous pycodestyle ansible-doc-extractor
[[ -e $(find test/ -name sanity.txt) ]] && pip install -r $(find test/ -name sanity.txt)

# place the modules in the appropriate folder
cp $DIR/plugins/modules/*.py $ANSIBLE_DIR/lib/ansible/modules/


set +e

rc=0
errored=""
for f in $DIR/plugins/modules/*.py; do
    f="${f##*/}"
    m_rc=0
    for version in $PY_VERSIONS; do
        echo "-------- sanity tests for $f ($version) --------"
        # remove potential ignore lines of core module
        grep "${f%%.py}" $SANITY_IGNORE && sed -i "/$f/d" $SANITY_IGNORE
        ansible-test sanity ${f%%.py} --python $version
        (( $? )) && m_rc=1 && rc=$(($rc + $m_rc))
    done
    (( $m_rc )) && errored+="$f "
done
(( $rc )) && printf "-------- module in error --------\n$errored\n"

set -e

deactivate

exit $rc
