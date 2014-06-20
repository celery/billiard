PYTHON=python

flakecheck:
	flake8 billiard

flakediag:
	-$(MAKE) flakecheck

flakepluscheck:
	flakeplus billiard --2.6

flakeplusdiag:
	-$(MAKE) flakepluscheck

flakes: flakediag flakeplusdiag

test:
	nosetests -xv billiard.tests

cov:
	nosetests -xv billiard.tests --with-coverage --cover-html --cover-branch

removepyc:
	-find . -type f -a \( -name "*.pyc" -o -name "*$$py.class" \) | xargs rm
	-find . -type d -name "__pycache__" | xargs rm -r

gitclean:
	git clean -xdn

gitcleanforce:
	git clean -xdf

bump_version:
	$(PYTHON) extra/release/bump_version.py billiard/__init__.py

distcheck: flakecheck test gitclean

dist: readme docsclean gitcleanforce removepyc
