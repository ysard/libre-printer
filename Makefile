test:
    pytest tests
	@#python setup.py test --addopts "tests libreprinter -vv"

coverage:
	pytest --cov=libreprinter -vv
	@#python setup.py test --addopts "--cov libreprinter tests"

run:
	python -m libreprinter

black:
	black libreprinter

doc:
	$(MAKE) -C ./docs html

# development & release cycle
fullrelease:
	fullrelease
install:
	@# Replacement for python setup.py develop which doesn't support extra_require keyword.
	@# Install a project in editable mode.
	pip install -e .[dev]
uninstall:
	pip libreprinter uninstall

check_setups:
	pyroma .

check_code:
	prospector libreprinter/
	check-manifest

missing_doc:
	# Remove D213 antagonist of D212
	prospector libreprinter/ | grep "libreprinter/\|Line\|Missing docstring"
