PROJECT_VERSION=$(shell python setup.py --version)
PACKAGE_NAME=libreprinter

# Workaround for targets with the same name as a directory
.PHONY: doc tests

# Tests
tests:
	LOG_LEVEL=DEBUG pytest tests
	@#python setup.py test --addopts "tests $(PACKAGE_NAME) -vv"

coverage:
	LOG_LEVEL=DEBUG pytest --cov=$(PACKAGE_NAME) --cov-report term-missing -vv
	@#python setup.py test --addopts "--cov $(PACKAGE_NAME) tests"
	@-coverage-badge -f -o images/coverage.svg

branch_coverage:
	LOG_LEVEL=DEBUG pytest --cov=$(PACKAGE_NAME) --cov-report term-missing --cov-branch -vv

docstring_coverage:
	interrogate -v $(PACKAGE_NAME)/ \
	    -e $(PACKAGE_NAME)/__init__.py \
	    -e $(PACKAGE_NAME)/handlers/__init__.py \
	    --badge-style flat --generate-badge images/

# Code formatting
black:
	black $(PACKAGE_NAME)

# Run the service locally
run:
	-killall convert-escp2
	python -m $(PACKAGE_NAME)

update_firmware:
	avrdude -v -patmega32u4 -cavr109 -P/dev/ttyACM0 -b57600 -D -Uflash:w:./firmware/libreprinter.ino.hex:i

clean:
	rm -rf eps pcl pdf png raw txt txt_jobs hpgl ps txt_stream dist csv $(PACKAGE_NAME).egg-info
	-$(MAKE) -C ./doc clean

doc:
	$(MAKE) -C ./doc html

# development & release cycle
fullrelease:
	@echo "\033[5;1;31m*** DO NOT forget to update debian/changelog version before! ***\033[0m"
	fullrelease
install:
	@# Replacement for python setup.py develop which doesn't support extra_require keyword.
	@# Install a project in editable mode.
	pip install -e .[dev]
uninstall:
	pip $(PACKAGE_NAME) uninstall

sdist:
	@echo Building the distribution package...
	python setup.py sdist

upload: clean sdist
	python setup.py bdist_wheel
	twine upload dist/* -r pypi

check_setups:
	pyroma .

check_code:
	prospector $(PACKAGE_NAME)/
	check-manifest

missing_doc:
	# Remove D213 antagonist of D212
	prospector $(PACKAGE_NAME)/ | grep "$(PACKAGE_NAME)/\|Line\|Missing docstring"

archive:
	# Create upstream src archive
	git archive HEAD --prefix='libre-printer-$(PROJECT_VERSION).orig/' | gzip > ../libre-printer-$(PROJECT_VERSION).orig.tar.gz

reset_patches:
	# Force the removal of the current patches
	-quilt pop -af

debianize: archive reset_patches
	dpkg-buildpackage -us -uc -b -d

debcheck:
	lintian -EvIL +pedantic ../libre-printer_*.deb


# development & testing
# Do not forget to use `send_end_config` directive to simulate the interface
# presence & response.
test_std_tty:
	# Allow stdin terminal to serial tty => manual debug
	socat PTY,link=./virtual-tty,raw,echo=0 -

test_tty_to_tty:
	# serial tty to serial tty => automatic test
	socat PTY,link=./virtual-tty,raw,echo=0 PTY,link=./input-tty,raw,echo=0

test_tty_to_rpi:
	# serial tty to serial tty => automatic test in chroot env
	socat PTY,link=/mnt/raspbian/home/pi/virtual-tty,raw,echo=0 PTY,link=./input-tty,raw,echo=0

prod_tty_to_tty:
	# serial interface => serial tty
	socat PTY,link=./virtual-tty,raw,echo=0 PTY,link=/dev/ttyUSB0,raw,echo=0

send_tty_input:
	# Send Test1.prn to ./virtual-tty
	./tools/input_tty_generator.py

send_end_config:
	# Send "end_config" word to end the interface configuration
	echo "end_config" >> input-tty
