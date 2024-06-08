PROJECT_VERSION=$(shell python setup.py --version)

# Workaround for targets with the same name as a directory
.PHONY: doc tests

# Tests
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

# Code formatting
black:
	black libreprinter

# Run the service locally
run:
	-killall convert-escp2
	python -m libreprinter

update_firmware:
	avrdude -v -patmega32u4 -cavr109 -P/dev/ttyACM0 -b57600 -D -Uflash:w:./firmware/libreprinter.ino.hex:i

clean:
	rm -rf eps pcl pdf png raw txt txt_jobs txt_stream dist
	-$(MAKE) -C ./doc clean

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

archive:
	# Create upstream src archive
	git archive HEAD --prefix='libre-printer-$(PROJECT_VERSION).orig/' | gzip > ../libre-printer-$(PROJECT_VERSION).orig.tar.gz

debianize: archive
	dpkg-buildpackage -us -uc -b -d

debcheck:
	lintian -EvIL +pedantic ../libre-printer_*.deb


# development & testing
test_std_tty:
	# Allow stdin terminal to serial tty => manual debug
	socat PTY,link=./virtual-tty,raw,echo=0 -

test_tty_to_tty:
	# serial tty to serial tty => automatic test
	socat PTY,link=./virtual-tty,raw,echo=0 PTY,link=./input-tty,raw,echo=0

test_tty_to_rpi:
	# serial tty to serial tty => automatic test in chroot env
	socat PTY,link=/mnt/raspbian/home/pi/libreprinter/virtual-tty,raw,echo=0 PTY,link=./input-tty,raw,echo=0

prod_tty_to_tty:
	# serial interface => serial tty
	socat PTY,link=./virtual-tty,raw,echo=0 PTY,link=/dev/ttyUSB0,raw,echo=0

send_tty_input:
	# Send Test1.prn to ./virtual-tty
	./input_tty_generator.py

send_end_config:
	# Send "end_config" word to end the interface configuration
	echo "end_config" >> input-tty
