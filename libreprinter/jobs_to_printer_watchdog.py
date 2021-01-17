"""Watchdog for /pdf directory that is able to sent new files to a printer"""
# Standard imports
import shlex
import subprocess
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import RegexMatchingEventHandler

# Custom imports
from libreprinter.commons import logger

LOGGER = logger()


class PdfTxtEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class only reimplement :meth:`on_created` event.

    Attribute:
        :param printer_name: Name of the CUPS printer which will receive files as jobs.
        :type printer_name: str

    Class attribute:
        :param FILES_REGEX: Patterns to detect pdf and txt files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*/pdf/.*\.pdf$", r".*/txt_jobs/.*\.txt$"]

    def __init__(self, printer_name=None, *args, **kwargs):
        super().__init__(regexes=self.FILES_REGEX, *args, **kwargs)
        self.printer_name = printer_name

    def on_closed(self, event):
        """PDF or TXT creation is detected, send it to the configured printer"""
        LOGGER.debug("Event detected: %s", event)

        # Directly build arg list; enquote src_path to avoid lpr error:
        # "lpr: No file in print request."
        args = ["/usr/bin/lpr", "-P", self.printer_name, shlex.quote(event.src_path)]
        try:
            # We are in a child thread, we can have blocking calls like run()
            # Capture all outputs from lpr in case of error with PIPE
            subprocess.run(
                args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True
            )
        except subprocess.CalledProcessError as e:
            # process exits with a non-zero exit code
            LOGGER.error("stdout: %s; stderr: %s", e.stdout, e.stderr)
            LOGGER.exception(e)


def setup_watchdog(config):
    """Initialise a watchdog on `/pdf` `/txt_jobs` directories in configured
    `output_path`.

    Any pdf or txt file created in these directories will be sent to the printer
    configured via `output_printer`.

    :return: Observer that is currently watching directories.
    :rtype: watchdog.Observer
    """
    LOGGER.info("Launch pdf & txt watchdog...")

    event_handler = PdfTxtEventHandler(
        printer_name=config["misc"]["output_printer"], ignore_directories=True
    )
    observer = InotifyObserver()
    # config["misc"]["output_path"] "/home/Lex/pdf/"
    observer.schedule(event_handler, config["misc"]["output_path"], recursive=True)
    observer.start()

    return observer


if __name__ == "__main__":

    obs = setup_watchdog(
        {"misc": {"output_path": "./", "output_printer": "TEST_PRINTER"}}
    )
    obs.join()
