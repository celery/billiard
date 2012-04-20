PYTHON?=python2.5
PYTHONPATH="Lib/"
RUNPYTHON=PYTHONPATH=$(PYTHONPATH) $(PYTHON)
BUILDER="html"

.PHONY=all inplace test clean realclean sdist examples doc

all: inplace

inplace: clean
	$(PYTHON) setup.py build_ext -i

test: inplace
	$(RUNPYTHON) -tt -c "from multiprocessing.tests import main; main()"

clean:
	find Lib/ \( -name '*.py[co]' -or -name '*.so' \) -exec rm {} \;
	rm -rf build/sphinx

realclean: clean
	find . \( -name '*~' -or -name '*.bak' -or -name '*.tmp' \) -exec rm {} \;
	rm -f MANIFEST
	rm -rf multiprocessing.egg-info
	rm -rf build/
	rm -rf dist/

sdist: realclean
	$(PYTHON) setup.py sdist --format=gztar
	$(PYTHON) setup.py sdist --format=zip

examples: inplace
	@echo -n "\n"
	@for EXAMPLE in distributing newtype pool synchronize benchmarks workers; do \
		echo "*** Running example mp_$${EXAMPLE}.py"; \
		$(RUNPYTHON) Doc/includes/mp_$${EXAMPLE}.py || exit 1; \
		echo -n "\n***********************\n\n"; \
	done

doc:
	mkdir -p Doc/static Doc/templates
	$(PYTHON) setup.py build_sphinx --builder=$(BUILDER) \
	    --source-dir=Doc/

