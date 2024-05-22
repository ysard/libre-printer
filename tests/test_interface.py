"""Test conversion process through the software interface interpreter"""
# Standard imports
import os
import time
import configparser
import shlex
import subprocess
from pathlib import Path
from threading import Thread
from multiprocessing import Process
from functools import partial
import pytest
from unittest.mock import patch

# Custom imports
from libreprinter.config_parser import parse_config, debug_config_file
from libreprinter.interface import (
    read_interface,
    build_interface_config_settings,
    apply_msb_control,
    is_bit_set,
)
from libreprinter.file_handler import init_directories
from libreprinter.legacy_interprocess_com import (
    initialize_interprocess_com,
    get_status_message,
    debug_shared_memory,
)
from libreprinter.plugins.lp_escp2_converter import launch_escp2_converter
from libreprinter.plugins.lp_pcl_to_pdf_watchdog import setup_pcl_watchdog
from libreprinter.plugins.lp_txt_converter import setup_text_watchdog

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
    ],
    ids=["defaultConfig"],
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


@pytest.fixture()
def tmp_process():
    """Yield new process ready to be started

    Assign `run` attribute to a target function before calling `start` method.
    The tearDown will automatically terminates this process.
    """
    process = Process()
    yield process
    process.terminate()


@pytest.fixture()
def slow_down_tests():
    yield
    time.sleep(1)


@pytest.fixture()
def extra_config(init_config, request):
    """Init configParser, init converter subprocess/watchdog if needed

    This fixture has a tearDown which ensures that the subprocess is killed
    between tests.

    :param init_config: temporary working dir + initialized config.
        See :meth:`init_config` fixture.
    :param request: Type of emulation (epson/hp/auto) and endlesstext param.
        These settings are added in config.
        With epson emulation, if endlesstext is "strip-escp2-stream"
        "strip-escp2-jobs" or "no", espc2 converter is launched in background.
        With hp emulation, if endlesstext is "no", pcl watchdog is launched in
        background.
        See `indirect` keyword arg of parametrized test
    :type init_config: tuple[str, configparser.ConfigParser]
    :type request: tuple[str, str]
    :return: Yield temporary directory and configParser
    :rtype: generator[tuple[str, configparser.ConfigParser]]
    """
    tmp_dir, config = init_config
    emulation, endlesstext = request.param

    # Add current emulation setting
    config["misc"]["emulation"] = emulation
    # Accelerate the test by reducing timeout
    config["misc"]["end_page_timeout"] = "1"
    # Add endless setting & converter path
    config["misc"]["endlesstext"] = endlesstext
    config["misc"]["escp2_converter_path"] = cm.ESCP2_CONVERTER
    config["misc"]["pcl_converter_path"] = cm.PCL_CONVERTER

    debug_config_file(config)

    if "escp2" in endlesstext or (emulation == "epson" and endlesstext == "no"):
        # Launch escp2 converter
        converter_process = launch_escp2_converter(config)
        yield (tmp_dir, config)
        converter_process.kill()
        return

    if emulation == "hp" and endlesstext == "no":
        # Launch pcl converter
        observer = setup_pcl_watchdog(config)
        yield (tmp_dir, config)
        observer.stop()
        return

    yield (tmp_dir, config)


@pytest.mark.timeout(10)
@pytest.mark.parametrize(
    "emulation, test_file",
    [
        ("epson", "escp2_1.prn"),
        ("epson", "test_page_escp2.prn"),
        # ("hp", "test_page_pcl.prn"),  # TODO: pas de sync converter .. How to test end of job ?
    ],
)
def test_interface_receiving(emulation, test_file, init_config, slow_down_tests):
    """Simulation of jobs with various emulation parameters

    This tests uses full pipeline with emulated serial interface.

    .. note:: About the exception `device reports readiness to read but returned
        no data (device disconnected or multiple access on port?)` from pyserial.
        This exception occurs only (?) on simulated mode on a virtual tty via
        socat.
        It seems to be solved via a timeout between tests and just after
        the start of the read_interface thread.

    :param emulation: Emulation type (epson, hp, auto)
    :param test_file: File sent to the interface. The result must be exactly the
        same. Files are stored in `<project_root_dir>/test_data/`.
    :param init_config: temporary working dir + initialized config.
        See :meth:`init_config` fixture.
    :type emulation: str
    :type test_file: str
    :type init_config: tuple[str, configparser.ConfigParser]
    """
    tmp_dir, config = init_config

    # Add current emulation setting
    config["misc"]["emulation"] = emulation

    debug_config_file(config)

    # Launch interface reader (infinite loop)
    interface_thread = Thread(target=partial(read_interface, config))
    interface_thread.start()

    LOGGER.debug("Thread started")
    # Fix minor exception from pyserial (See docstring note)
    time.sleep(2)
    # Put data in input-tty
    with open(DIR_DATA + test_file, "rb") as f_d, \
            open(tmp_dir + "input-tty", "wb") as tty_f_d:
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


@pytest.mark.timeout(10)
@patch("libreprinter.interface.get_serial_handler", lambda x: True)
@patch("libreprinter.interface.configure_interface", lambda x, y: None)
@pytest.mark.parametrize(
    "extra_config, in_file, expected_file, out_file, repetitions",
    [
        ## Pdf files generation
        (("epson", "no"), "escp2_1.prn", "escp2_1.pdf", "pdf/page1-1.pdf", 1),
        (("hp", "no"), "test_page_pcl.prn", 14141, "pdf/1.pdf", 1),
        ## Plain text tests
        (("epson", "plain-stream"), "escp2_1.prn", "escp2_1_plain.txt", "txt_stream/1.txt", 1),
        # 1 file plain text repeated 2 times in a stream
        (("epson", "plain-stream"), "escp2_1.prn", "escp2_1_plain.txt", "txt_stream/1.txt", 2),
        (("epson", "plain-jobs"), "escp2_1.prn", "escp2_1_plain.txt", "txt_jobs/1.txt", 1),
        ## Stripped text tests
        (("epson", "strip-escp2-stream"), "escp2_1.prn", "escp2_1_strip.txt", "txt_stream/1.txt", 1),
        # 1 file stripped repeated 2 times in a stream
        (("epson", "strip-escp2-stream"), "escp2_1.prn", "escp2_1_strip.txt", "txt_stream/1.txt", 2),
        (("epson", "strip-escp2-jobs"), "escp2_1.prn", "escp2_1_strip.txt", "txt_jobs/1.txt", 1),
        ## pcl data with epson config
        (("hp", "plain-stream"), "test_page_pcl.prn", "test_page_pcl.prn", "pcl/1.pcl", 1),
        # TODO: epson/hp/auto ?
    ],
    # First param goes in the 'request' param of the fixture extra_config
    indirect=["extra_config"],
    ids=[
        "epson-pdf", "hp-pdf", "plain-stream*1", "plain-stream*2", "plain-jobs",
        "strip-escp2-stream*1", "strip-escp2-stream*2", "strip-escp2-jobs", "pcl"
    ]
)
def test_endlesstext_values(extra_config, in_file, expected_file, out_file, repetitions, tmp_process):
    """Test the generation of files according to emulation and endlesstext settings

    Mocks:
        - get_serial_handler: do nothing
        - configure_interface: do nothing
        - get_buffer: return simulated databytes

    :param extra_config: (fixture) Temporary directory, configParser
        and converter launcher.
    :param in_file: File containing simulated input content
    :param expected_file: File containing expected content for out_file
        Some files (pdfs generated by ghosscript) contain timestamps
        and can't be tested easly... In this case we only use the expected size
        in bytes...
    :param out_file: Expected path and filename generated by the printer
    :param repetitions: Number of simulated versions of in_file content sent
    :param tmp_process: (fixture) Process waiting a reimplementation of `run`
    :type extra_config: tuple[str, configparser.ConfigParser]
    :type in_file: str
    :type expected_file: str
    :type out_file: str
    :type repetitions: int
    :type tmp_process: multiprocessing.Process
    """
    tmp_dir, config = extra_config

    raw_content = Path(DIR_DATA + in_file).read_bytes()

    def mock_interface_buffer(file_handler, timeout, counter=[0], *args, **kwargs):
        """Mock function for :meth:`libreprinter.interface.get_buffer`

        Simulate the reception of databytes corresponding to 1 page for each call.

        - Count the number of calls
        - If the number is <= to a repetition number: return raw_content
        - Otherwise return None (=> end of page timeout signal)
        """
        counter[0] += 1
        time.sleep(1)
        if counter[0] <= repetitions:
            return raw_content

    def wrapper(config):
        """Wrapper used to patch the get_buffer function inside the new process"""
        with patch("libreprinter.interface.get_buffer", mock_interface_buffer):
            read_interface(config)

    tmp_process.run = partial(wrapper, config)
    tmp_process.start()
    LOGGER.debug("Process started")

    # Test obtained files existence
    processed_file = Path(tmp_dir) / out_file
    while not processed_file.exists() or processed_file.stat().st_size == 0:
        time.sleep(1 * repetitions + 3)  # Empirical delay
        print("Waiting dir tree: ", set(Path(tmp_dir).rglob("*")))

    ret = set(Path(tmp_dir).rglob("*"))
    print("Dir tree: ", ret)
    found_stats = processed_file.stat()
    print("Processed file & found stats:", processed_file, found_stats)
    if isinstance(expected_file, int):
        # Fallback for pdfs from ghostscript (see doc)
        # Check only the expected size
        assert found_stats.st_size == expected_file
        return

    # Check file content
    expected_content = Path(DIR_DATA + expected_file).read_bytes()
    assert expected_content * repetitions == processed_file.read_bytes(), \
        "Maybe a mismatch on the Haru Free PDF Library?"


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
            ["delayprinter=0\n"],
        ),
        (
            """
            [misc]
            [parallel_printer]
            [serial_printer]
            ; Manually enabled
            enabled=yes
            """,
            ["dtr_logic=1\n", "serial_enabled=1\n", "baudrate=19200\n", "flow_control=1\n"],
        ),
    ],
    ids=["serial_disabled", "serial_enabled"],
)
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


def test_apply_msb_control():
    """Test msb modifications from escp datasheet (deprecated)"""
    # Do nothing
    found = apply_msb_control(b"\xff", msbsetting=0)
    assert found == b"\xff"

    # MSB is set: bit 7 to 0
    found = apply_msb_control(b"\xff", msbsetting=1)
    assert found == 0b01111111  # 255 => 127

    # MSB is set: bit 7 to 1
    # /!\ Beware with this one, we want an unsigned int: 255, not -1
    found = apply_msb_control(b"\xfe", msbsetting=2)
    assert found == 0b11111111  # 254 => 255

    # Wrong msbsetting
    with pytest.raises(ValueError, match=r"msbsetting value not expected:.*"):
        _ = apply_msb_control(b"\xff", msbsetting=3)


@pytest.mark.timeout(6)
def test_bad_serial_port():
    """Test inexistant serial port"""
    # Get default settings
    config = configparser.ConfigParser()
    [config.add_section(section) for section in ("misc", "parallel_printer", "serial_printer")]
    config = parse_config(config)

    # Replace serial_port setting with a non-existent port
    config["misc"]["serial_port"] = ""

    # 5 tries in 5 seconds before returning None
    ret = read_interface(config)
    assert ret is None


def test_is_bit_set():
    found = is_bit_set(b"\x01", 0)
    assert found

    found = is_bit_set(b"\x01", 1)
    assert not found
