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

echo "Building index.html with TRAVIS_REPO_SLUG=$TRAVIS_REPO_SLUG"
cat > $DOC_DIR/index.html <<- _EOF_
<html>
  <head>
    <meta charset="UTF-8">
    <title>Ansible for power AIX</title>
  </head>
  <body>
    <h1>Ansible for power AIX</h1>
    <h2>Modules documentation</h2>
    <ul id="doc_list">
    </ul>
    <script>
      (async () => {
        const response = await fetch('https://api.github.com/repos/$TRAVIS_REPO_SLUG/contents?ref=gh-pages');
        const data = await response.json();
        let htmlString = '<ul>';
        for (let file of data) {
          if (file.path == 'index.html') continue;
          const fileName = file.path.replace('.txt', '');
          htmlString += \`<li><a href="\${file.path}">\${fileName}</a></li>\`;
        }
        htmlString += '</ul>';
        document.getElementById('doc_list').innerHTML = htmlString;
      })()
    </script>
  <body>
</html>
_EOF_

exit $rc
