#
# Copyright (c) IBM Corporation 2020
#

all:
	mkdir -p source/modules
	ansible-doc-extractor --template templates/module.rst.j2 source/modules ../plugins/modules/*.py
	sphinx-build -b html source build
	touch build/.nojekyll

clean:
	rm -rf build
	rm -rf source/modules/*.rst
