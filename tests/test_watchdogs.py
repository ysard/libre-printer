# Libreprinter is a software allowing to use the Centronics and serial printing
# functions of vintage computers on modern equipement through a tiny hardware
# interface.
# Copyright (C) 2020-2024  Ysard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Test watchdog behaviors

Test only file detections & startups.
"""
# Standard imports
import time
import pytest
from unittest.mock import patch

# Custom imports
from libreprinter.file_handler import init_directories
from libreprinter.plugins.lp_jobs_to_printer_watchdog import setup_pdf_watchdog
from libreprinter.plugins.lp_pcl_to_pdf_watchdog import setup_pcl_watchdog
from libreprinter.plugins.lp_txt_converter import setup_text_watchdog
from libreprinter.commons import PCL_CONVERTER, ENSCRIPT_BINARY

# Import create dir fixture
from .test_file_handler import temp_dir

CATCHED_EVENTS = list()


def mock_on_closed(self, event):
    """Show catched event, see :meth:`test_setup_watchdog`"""
    print("Catched event:", event)
    CATCHED_EVENTS.append(event)


@pytest.fixture()
def reset_catched_events():
    """Reset the global CATCHED_EVENTS variable for the next test"""
    global CATCHED_EVENTS
    CATCHED_EVENTS = list()


@pytest.mark.timeout(3)
@patch("libreprinter.plugins.lp_jobs_to_printer_watchdog.PdfEventHandler.on_closed", mock_on_closed)
@patch("libreprinter.plugins.lp_pcl_to_pdf_watchdog.PclEventHandler.on_closed", mock_on_closed)
@patch("libreprinter.plugins.lp_txt_converter.TxtEventHandler.on_closed", mock_on_closed)
@pytest.mark.parametrize(
    # WARNING: expected_file is currently NOT tested!
    "watchdog, config, files_to_create, expected_file",
    [
        # lp_jobs_to_printer_watchdog: Test the detection of a pdf file creation in /pdf
        (
            setup_pdf_watchdog,
            {"misc": {"output_printer": ""}},
            ["pdf/aaa", "pdf/a.pdf"],  # Last file is the good one
            None,  # File is sent to the printer via lpr => no expected file
        ),
        # lp_pcl_to_pdf_watchdog: Test the detection of pcl file creation in /pcl
        (
            setup_pcl_watchdog,
            {"misc": {"pcl_converter_path": PCL_CONVERTER}},
            ["pcl/aaa", "pcl/b.pcl"],  # Last file is the good one
            "pdf/b.pdf",
        ),
        # lp_txt_converter: Test the detection of txt file creation in /txt_jobs
        (
            setup_text_watchdog,
            {"misc": {"enscript_path": ENSCRIPT_BINARY, "enscript_settings": "-BR"}},
            ["txt_jobs/aaa", "txt_jobs/c.txt"],  # Last file is the good one
            "pdf/c.pdf",
        ),
    ],
    ids=["jobs_to_printer_watchdog", "pcl_to_pdf_watchdog", "txt_to_pdf_watchdog"],
)
def test_setup_watchdog(
    watchdog, config, files_to_create, expected_file, temp_dir, reset_catched_events
):
    """Test the detection of pdf creation in /pdf

    `on_closed` method is modified to show catched event instead of doing things;
    see :meth:`mock_on_closed`.

    .. warning:: Only the watchdog behaviors are tested here. What they do
        after the event detection is NOT tested here since `on_closed` callback
        is mocked (see :meth:`test_interface` module instead for more global tests).

    :param watchdog: Function that set up a watchdog according to a given config
    :param config: Config in the format returned by a Configuration Parser.
        Not all settings are required for a specific watchdog.
    :param files_to_create: List of files to create to wake up the watchdog.
        Last file is the good one.
    :param expected_file: Expected file in files_to_create that should be recognized
        by the watchdog. (NOT used for now).
    :param temp_dir: (fixture) Create temp directory
    :param reset_catched_events: (fixture) Force CATCHED_EVENTS global variable
        to be reset for each test.
    :type watchdog: <function>
    :type config: <dict>
    :type files_to_create: <list <str>>
    :type expected_file: <str>
    :type temp_dir: <str>
    :type reset_catched_events: <_pytest.logging.LogCaptureFixture>
    """
    init_directories(temp_dir)

    # Add temporary dir to config
    config["misc"]["output_path"] = temp_dir
    # Start watchdog
    ret = watchdog(config)

    # Only x.pdf should be catched
    [open(temp_dir + filename, "a").close() for filename in files_to_create]

    while not CATCHED_EVENTS:
        time.sleep(0.5)

    # Check detection of the correct file
    assert len(CATCHED_EVENTS) == 1
    good_created_file = files_to_create[-1]
    assert good_created_file in CATCHED_EVENTS[0].src_path

    # Tear down the watchdog
    ret.stop()

    # Check the watchdog processing => not the purpose of THIS test,
    # but may be tested in another test that will not test only the on_closed callback!
    # if expected_file:
    #     time.sleep(2)
    #     print(Path(temp_dir + "pdf/"))
    #     found_files = list(str(path) for path in Path(temp_dir + "pdf/").glob("*"))[0]
    #     assert expected_file in found_files


def test_bad_printer(temp_dir, caplog):
    """Test with not existent printer

    lpr program should return an error

    :param temp_dir: (fixture) Create temp directory
    :param caplog: (fixture) pytest caplog-fixture
    :type temp_dir: <str>
    :type caplog: <_pytest.logging.LogCaptureFixture>
    """
    init_directories(temp_dir)

    setup_pdf_watchdog(
        {"misc": {"output_path": temp_dir, "output_printer": "Fake_Printer_Name"}}
    )

    open(temp_dir + "pdf/x.pdf", "a").close()
    time.sleep(0.5)

    # We expect an exception in the logger returned by the lpr program
    print(caplog.text)
    assert "returned non-zero exit status 1" in caplog.text


@pytest.mark.parametrize(
    "watchdog, config, expected_exception_text, expected_log_text",
    [
        (
            setup_pcl_watchdog,
            {"misc": {"pcl_converter_path": "/usr/bin/Fake_Converter_Name"}},
            r"pcl converter not found",
            "Setting <pcl_converter_path:",
        ),
        (
            setup_text_watchdog,
            {"misc": {"enscript_path": "/usr/bin/Fake_Converter_Name"}},
            r"enscript converter not found",
            "Setting <enscript_path:",
        ),
    ],
    ids=["bad_pcl_binary", "bad_enscript_binary"],
)
def test_bad_binary_path(
    watchdog, config, expected_exception_text, expected_log_text, temp_dir, caplog
):
    """Test setup_*_watchdog functions with non-existent binaries

    The watchdog should crash emitting a FileNotFoundError exception.

    :param watchdog: Function that set up a watchdog according to a given config
    :param config: Config in the format returned by a Configuration Parser.
        Not all settings are required for a specific watchdog.
    :param expected_exception_text: Exception message in a raw string.
    :param expected_log_text: Fragment of a message emitted by the logger.
    :param temp_dir: (fixture) Create temp directory
    :param caplog: (fixture) pytest caplog-fixture
    :type watchdog: <function>
    :type config: <dict>
    :type expected_exception_text: <str>
    :type expected_log_text: <str>
    :type temp_dir: <str>
    :type caplog: <_pytest.logging.LogCaptureFixture>
    """
    init_directories(temp_dir)

    # FileNotFoundError is expected when launching the watchdog
    with pytest.raises(FileNotFoundError, match=expected_exception_text):
        # Add temporary dir to config
        config["misc"]["output_path"] = temp_dir
        # Start watchdog
        _ = watchdog(config)
        # Failure is expected: no need to stop the watchdog

    # We expect an error in the logger
    print(caplog.text)
    assert expected_log_text in caplog.text
