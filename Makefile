# Workaround for targets with the same name as a directory
.PHONY: doc tests

tests:
	pytest tests
	@#python setup.py test --addopts "tests libreprinter -vv"

coverage:
	pytest --cov=libreprinter --cov-report term-missing -vv
	@#python setup.py test --addopts "--cov libreprinter tests"
	@-coverage-badge -f -o images/coverage.svg

docstring_coverage:
	interrogate -v libreprinter/ \
	    -e libreprinter/__init__.py \
	    -e libreprinter/handlers/__init__.py \
	    --badge-style flat --generate-badge images/

black:
	black libreprinter

run:
	-killall convert-escp2
	python -m libreprinter

update_firmware:
	avrdude -v -patmega32u4 -cavr109 -P/dev/ttyACM0 -b57600 -D -Uflash:w:./firmware/libreprinter.ino.hex:i

clean:
	rm -rf eps pcl pdf png raw txt txt_jobs txt_stream dist
	$(MAKE) -C ./doc clean

doc:
	$(MAKE) -C ./doc html

# development & release cycle
fullrelease:
	fullrelease
install:
	@# Replacement for python setup.py develop which doesn't support extra_require keyword.
	@# Install a project in editable mode.
	pip install -e .[dev]
uninstall:
	pip libreprinter uninstall

sdist:
	@echo Building the distribution package...
	python setup.py sdist

upload: clean sdist
	python setup.py bdist_wheel
	twine upload dist/* -r pypi

check_setups:
	pyroma .

check_code:
	prospector libreprinter/
	check-manifest

missing_doc:
	# Remove D213 antagonist of D212
	prospector libreprinter/ | grep "libreprinter/\|Line\|Missing docstring"

debianize:
	dpkg-buildpackage -us -uc -b -d

debcheck:
	lintian -EvIL +pedantic ../libre-printer_*.deb
