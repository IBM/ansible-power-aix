#
# SPDX-License-Identifier: Apache-2.0
#

all:
	ansible-doc-extractor --template templates/module.rst.j2 source/modules ../plugins/modules/*.py
	sphinx-build -b html source build
	touch build/.nojekyll

clean:
	rm -rf build
	rm -rf source/modules/*.rst
