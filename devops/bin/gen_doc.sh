#!/bin/bash

set -x
set -o errexit
set -o pipefail
set -o errtrace

OUTPUTDIR=./documentation

err_report() {
    echo "Error running '$1' [rc=$2] line $3 "
}

trap 'err_report "$BASH_COMMAND" $? $LINENO' ERR

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
MODULE_DIR="$HOME/.ansible/plugins/modules"

echo "DIR=$DIR"

[[ ! -d $MODULE_DIR ]] && mkdir -p $MODULE_DIR

cp library/emgr.py $MODULE_DIR
ansible-doc -t module emgr


