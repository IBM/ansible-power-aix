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
MODULE_DIR="$DIR/plugins/modules"
DOC_DIR="$DIR/docs"
DOC_SRC_DIR="$DIR/docs/source"
DOC_BLD_DIR="$DIR/docs/build"
DOC_TEMPLATE="$DIR/docs/templates/module.rst.j2"

# There is an issue with templates/module.rst.j2
# ansible-doc-extractor --template $DOC_TEMPLATE $DOC_SRC_DIR $MODULE_DIR/*.py
[[ ! -d $DOC_SRC_DIR/modules ]] && mkdir -p $DOC_SRC_DIR/modules
[[ ! -d $DOC_BLD_DIR ]] && mkdir -p $DOC_BLD_DIR
ansible-doc-extractor $DOC_SRC_DIR/modules $MODULE_DIR/*.py
sphinx-build -b html $DOC_SRC_DIR $DOC_BLD_DIR
touch $DOC_BLD_DIR/.nojekyll

exit $rc
