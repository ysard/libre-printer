# Libreprinter is a software allowing to use the Centronics and serial printing
# functions of vintage computers on modern equipement through a tiny hardware
# interface.
# Copyright (C) 2020-2022  Ysard
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
from unittest.mock import patch

# Custom imports
from libreprinter.file_handler import init_directories
from libreprinter.jobs_to_printer_watchdog import setup_watchdog

# Import create dir fixture
from .test_file_handler import temp_dir

CATCHED_EVENTS = list()


def mock_on_closed(self, event):
    """Show catched event, see :meth:`test_setup_watchdog`"""
    print(event)
    CATCHED_EVENTS.append(event)


@patch("libreprinter.jobs_to_printer_watchdog.PdfTxtEventHandler.on_closed", mock_on_closed)
def test_setup_watchdog(temp_dir):
    """Test the detection of pdf creation in /pdf

    `on_closed` method is modified to show catched event instead of redirecting
    pdf to a Cups printer.
    """
    init_directories(temp_dir)

    # on_closed = mock_on_closed
    setup_watchdog({"misc": {"output_path": temp_dir, "output_printer": None}})

    # Only x.pdf should be catched
    open(temp_dir + "pdf/aaa", "a").close()
    open(temp_dir + "pdf/x.pdf", "a").close()

    while not CATCHED_EVENTS:
        time.sleep(0.5)

    assert "pdf/x.pdf" in CATCHED_EVENTS[0].src_path

    assert len(CATCHED_EVENTS) == 1
    print(CATCHED_EVENTS)


def test_bad_printer(temp_dir, caplog):
    """Test with not existent printer

    :param caplog: pytest caplog-fixture
    :type caplog: <_pytest.logging.LogCaptureFixture>
    """
    init_directories(temp_dir)

    setup_watchdog({"misc": {"output_path": temp_dir, "output_printer": "Fake_Printer_Name"}})

    open(temp_dir + "pdf/x.pdf", "a").close()
    time.sleep(0.5)

    # We expect an exception in the logger returned by the lpr program
    print(caplog.text)
    assert "returned non-zero exit status 1" in caplog.text
