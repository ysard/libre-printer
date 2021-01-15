"""Test conversion process through interface interpreter
"""
# Standard imports
import os
import time
import configparser
import shlex
import subprocess
from threading import Thread
from functools import partial
import pytest
from unittest.mock import patch
# Custom imports
from libreprinter.config_parser import parse_config, debug_config_file
from libreprinter.interface import read_interface, build_interface_config_settings
from libreprinter.file_handler import init_directories
from libreprinter.legacy_interprocess_com import initialize_interprocess_com, \
    get_status_message, debug_shared_memory
import libreprinter.commons as cm
# Import create dir fixture
from .test_file_handler import temp_dir

LOGGER = cm.logger()

DIR_DATA = os.path.dirname(os.path.abspath(__file__)) + "/../test_data/"  # current package name


@pytest.fixture()
def init_virtual_interface(temp_dir):
    """Init virtual serial interface

    Setup socat virtual interface in a temporary working dir thanks to
    :meth:`.test_file_handler.tempr_dir` fixture.

    :param temp_dir: Path of temporary working dir returned by pytest fixture.
    :type temp_dir: str
    """
    # serial tty to serial tty => automatic test
    cmd = "socat PTY,link={}virtual-tty,raw,echo=0 PTY,link={}input-tty,raw,echo=0".format(temp_dir, temp_dir)
    args = shlex.split(cmd)

    # Non blocking call => socat will be executed in background
    p = subprocess.Popen(args)
    # 0 or -N if process is terminated (this should not be the case here)
    assert p.returncode is None

    yield temp_dir

    # Tear down: kill socat
    # (tty files removal is done in the tear down of temp_dir)
    p.kill()


@pytest.fixture(
    params=[
        """
        [misc]
        [parallel_printer]
        [serial_printer]
        """,
    ]
)
def init_config(request, init_virtual_interface):
    """Return temporary working dir + initialized config

    :return: Temp dir, thanks to :meth:`init_virtual_interface` fixture,
        and initialized config.
    :rtype: str, configparser.ConfigParser
    """
    tmp_dir = init_virtual_interface

    config = configparser.ConfigParser()
    config.read_string(request.param)

    # Specific test settings
    config["misc"]["output_path"] = tmp_dir
    config["misc"]["serial_port"] = tmp_dir + "virtual-tty"
    config["misc"]["end_page_timeout"] = "1"  # Expect 1 page only: speed up test

    # Set default values
    config = parse_config(config)

    # Prepare working directories
    init_directories(tmp_dir)

    # Erase shm file to purge previous jobs
    if os.path.exists("/dev/shm/" + cm.SHARED_MEM_NAME):
        os.remove("/dev/shm/" + cm.SHARED_MEM_NAME)
    initialize_interprocess_com()

    return tmp_dir, config


@pytest.mark.timeout(10)
@patch('serial.Serial.dtr')
@pytest.mark.parametrize(
    "emulation, test_file",
    [
        ("epson", "escp2_1.prn"),
        ("epson", "test_page_escp2.prn"),
        # ("hp", "test_page_pcl.prn"),  # TODO: pas de sync converter .. comment vérifier si le job est fini ?
    ],
)
def test_interface_receiving(dtr, emulation, test_file, init_config):
    """Simulation of jobs with various emulation parameters

    :param emulation: Emulation type (epson, hp, auto)
    :param test_file: File sent to the interface. The result must be exactly the
        same. Files are stored in `<project_root_dir>/test_data/`.
    :param init_config: temporary working dir + initialized config.
        See :meth:`init_config`.
    :type emulation: str
    :type test_file: str
    :type init_config: tuple[str, str]
    """
    tmp_dir, config = init_config

    # Add current emulation setting
    config["misc"]["emulation"] = emulation

    debug_config_file(config)

    # Launch interface reader
    # Assert the DTR line is not functional after opening the serial connection
    # on emulated interface, so it needs to be patched for tests.
    dtr.return_value = True
    interface_thread = Thread(target=partial(read_interface, config))
    interface_thread.start()

    LOGGER.debug("Thread started")
    # TODO check minor exception from pyserial:
    #   device reports readiness to read but returned no data
    #   (device disconnected or multiple access on port?)

    # Put data in input-tty
    with open(DIR_DATA + test_file, "rb") as f_d, open(
            tmp_dir + "input-tty", "wb") as tty_f_d:
        tty_f_d.write(b"end_config\n")  # Cheat about config ack from interface
        expected_content = f_d.read()
        tty_f_d.write(expected_content)

    # Wait end of receiving
    while get_status_message(202) == 0:
        time.sleep(1)
    debug_shared_memory()

    # Interface has a job for the converter
    assert get_status_message(202) == 1

    # Compare obtained file
    with open(tmp_dir + "raw/1.raw", "rb") as f_d:
        found_content = f_d.read()

    assert expected_content == found_content

    if emulation == "hp":
        # Check copy in pcl dir
        assert os.path.exists("pcl/1.pcl")


@pytest.mark.parametrize(
    "sample_config, expected",
    [
        (
            """
            [misc]
            [parallel_printer]
            [serial_printer]
            ; Default
            enabled=no
            """,
            ['delayprinter=0\n'],
        ),
        (
            """
            [misc]
            [parallel_printer]
            [serial_printer]
            ; Manually enabled
            enabled=yes
            """,
            ['dtr_logic=0\n', 'serial_enabled=1\n', 'baudrate=19200\n']
        )
    ]
    , ids=["serial_disabled", "serial_enabled"])
def test_get_interface_config(sample_config, expected):
    """Test the build of settings from config file, ready to be sent to the interface

    :param sample_config: Config string; equiv of config file.
    :param expected: List of processed settings.
    :type sample_config: str
    :type expected: list[str]
    """
    config = configparser.ConfigParser()
    config.read_string(sample_config)

    config = parse_config(config)

    # Get settings
    found_settings = build_interface_config_settings(config)
    print(found_settings)
    assert expected == found_settings
