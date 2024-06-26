#  Libreprinter is a software allowing to use the Centronics and serial printing
#  functions of vintage computers on modern equipement through a tiny hardware
#  interface.
#  Copyright (C) 2020-2024  Ysard
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Watchdog for /pdf directory that is able to sent new files to a printer

Send new pdfs files on a printer configured in Cups.

Expected settings: `output_printer` set and not `*stream` as endlesstext setting;
i.e. `output_printer` is defined; and it is not an infinite stream.

In other terms, a pdf is sent to printer if:

- `endlesstext` setting is `no`, `plain-jobs`, `strip-escp2-jobs`,
- and `output_printer` setting is not `no`

TODO: only "no" for endless config because strip wrongly builds empty pdf files
    => not any of ("plain-jobs", "strip-escp2-jobs", "no")
"""
# Standard imports
import shlex
import subprocess
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import RegexMatchingEventHandler

# Custom imports
from libreprinter import plugins_handler
from libreprinter.commons import logger

LOGGER = logger()

CONFIG = {
    "misc": {
        "output_printer": lambda param: param != "no",
        "endlesstext": ("no", "plain-jobs", "strip-escp2-jobs"),
    }
}


class PdfEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class only reimplement :meth:`on_created` event.

    Watched directories:

        - `pdf`: `*.pdf`

    Attribute:
        :param printer_name: Name of the CUPS printer which will receive files as jobs.
        :type printer_name: str

    Class attribute:
        :param FILES_REGEX: Patterns to detect pdf files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*/pdf/.*\.pdf$",]

    def __init__(self, *args, printer_name=None, **kwargs):
        """Constructor override
        Just add printer_name attr and define watchdog regexes.
        """
        super().__init__(*args, regexes=self.FILES_REGEX, **kwargs)
        self.printer_name = printer_name

    def on_closed(self, event):
        """PDF creation is detected, send it to the configured printer"""
        LOGGER.info("Event detected: %s", event)

        # Directly build arg list; enquote src_path to avoid lpr error:
        # "lpr: No file in print request."
        args = ["/usr/bin/lpr", "-P", self.printer_name, shlex.quote(event.src_path)]
        LOGGER.debug("lpr command: %s", args)
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


@plugins_handler.register
def setup_pdf_watchdog(config):
    """Initialise a watchdog on `/pdf` directory in configured
    `output_path`.

    Any pdf file created in these directories will be sent to the printer
    configured via `output_printer`.

    :return: Observer that is currently watching directories.
    :rtype: watchdog.Observer
    """
    LOGGER.info("Launch pdf watchdog...")

    event_handler = PdfEventHandler(
        printer_name=config["misc"]["output_printer"], ignore_directories=True
    )
    # Attach event handler to the configured output_path
    observer = InotifyObserver()
    observer.schedule(event_handler, config["misc"]["output_path"], recursive=True)
    observer.start()
    return observer


if __name__ == "__main__":  # pragma: no cover

    obs = setup_pdf_watchdog(
        {"misc": {"output_path": "./", "output_printer": "TEST_PRINTER"}}
    )
    obs.join()
