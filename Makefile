PROJ=billiard
PYTHON=python

flakecheck:
	flake8 "$(PROJ)"

flakediag:
	-$(MAKE) flakecheck

flakepluscheck:
	flakeplus --2.6 "$(PROJ)"

flakeplusdiag:
	-$(MAKE) flakepluscheck

flakes: flakediag flakeplusdiag

test:
	nosetests -xv

cov:
	nosetests -xv --with-coverage --cover-html --cover-branch

removepyc:
	-find . -type f -a \( -name "*.pyc" -o -name "*$$py.class" \) | xargs rm
	-find . -type d -name "__pycache__" | xargs rm -r

gitclean:
	git clean -xdn

gitcleanforce:
	git clean -xdf

distcheck: flakecheck test gitclean

dist: gitcleanforce removepyc
