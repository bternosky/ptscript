PYTHON ?= python3.11

all: qa

###########################################################################
# QA Tooling
###########################################################################
format:
	- $(PYTHON) -m black .

lint:
	- $(PYTHON) -m flake8 .

mypy:
	- $(PYTHON) -m mypy -m genreport

# Note: general QA should skip integration
qa: format lint mypy

###########################################################################
# Other utils
###########################################################################
clean:
	- find . -name "*~" | xargs rm -f
	- find . -name "*.pyc" | xargs rm -f

realclean: clean
	- find . -name '__pycache__' | xargs rm -rf
	- find . -name '.mypy_cache' | xargs rm -rf
	- find . -name '.pytest_cache' | xargs rm -rf
