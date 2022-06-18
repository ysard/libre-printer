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
