#!/bin/bash

echo "======== $0 ========"
set -x
set -o errexit
set -o pipefail
set -o errtrace


err_report() {
    echo "Error running '$1' [rc=$2] line $3 "
}

trap 'err_report "$BASH_COMMAND" $? $LINENO' ERR

DIR="$(pwd)"
MODULE_DIR="$HOME/.ansible/plugins/modules"
DOC_DIR="$DIR/documentation"

# place the modules in the appropriate folder
[[ ! -d $MODULE_DIR ]] && mkdir -p $MODULE_DIR
cp $DIR/library/*.py $MODULE_DIR/

# generate the documentation
[[ ! -d $DOC_DIR ]] && mkdir -p $DOC_DIR
set +e
rc=0
for f in $DIR/library/*.py; do
    f="${f##*/}"
    echo "-------- ansible-doc for $f --------"
    ansible-doc -t module ${f%%.py} >$DOC_DIR/${f%%.py}.txt
    rc=$(($rc + $?))
done
set -e

# check if we can push


exit $rc
