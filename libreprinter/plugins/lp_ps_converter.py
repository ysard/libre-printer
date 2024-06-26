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
"""Watchdog for /ps directory that is able to convert new files into pdfs

Conversions are made thanks to Ghostscript.

As soon as a file is closed, a pdf is created.

Expected config (emulation + endlesstext):

    - postscript + no
"""
# Standard imports
import shlex
from pathlib import Path
import subprocess
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import RegexMatchingEventHandler

# Custom imports
from libreprinter import plugins_handler
from libreprinter.file_handler import init_directories
from libreprinter.commons import logger

LOGGER = logger()

CONFIG = {
    "misc": {
        "emulation": ("postscript",),
        "endlesstext": ("no",),
    }
}
REQUIRED_DIRS = ["ps", ]


class PostscriptEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class only reimplement :meth:`on_created` event.

    Watched directory:

        - `ps`: `*.ps`

    Attribute:
        :param gs_settings: Command line settings for Ghostscript binary.
        :type gs_settings: list[str] or None

    Class attribute:
        :param FILES_REGEX: Patterns to detect postscript files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*\.ps$"]

    def __init__(self, *args, gs_settings=None, **kwargs):
        """Constructor override
        Just add Ghostscript settings attr and define watchdog regexes.
        """
        super().__init__(*args, regexes=self.FILES_REGEX, **kwargs)
        self.gs_settings = gs_settings or []

    def on_closed(self, event):
        """File closing is detected, convert it to PDF

        Minimal command::

            gs -sDEVICE=pdfwrite -o out.pdf in.ps
        """
        LOGGER.info("Event detected: %s", event)

        # Directly build arg list; enquote paths to avoid errors
        src_path = Path(event.src_path)
        pdf_path = src_path.parent / "../pdf" / (src_path.stem + ".pdf")
        ghostscript_cmd = [
            "/usr/bin/gs",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-sColorConversionStrategy=RGB",
            "-dCompatibilityLevel=1.7",  # Fix for reproductibility
            "-dEmbedAllFonts=true",  # Increase the final size
            "-dSubsetFonts=true",  # Reduce the final size
            f"-sOutputFile={shlex.quote(str(pdf_path))}",
        ]
        ghostscript_cmd += self.gs_settings
        ghostscript_cmd += [
            shlex.quote(event.src_path),
            "-c",
            "quit"
        ]
        LOGGER.debug("ghostscript command: %s", ghostscript_cmd)
        try:
            # We are in a child thread, we can have blocking calls like run()
            # Capture all outputs from the command in case of error with PIPE
            subprocess.run(
                ghostscript_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True
            )
        except subprocess.CalledProcessError as e:
            # process exits with a non-zero exit code
            LOGGER.error("stdout: %s; stderr: %s", e.stdout, e.stderr)
            LOGGER.exception(e)


@plugins_handler.register
def setup_postscript_watchdog(config):
    """Initialise a watchdog on `/ps` directory in configured `output_path`.

    Any ps file created in this directories will be converted in `/pdf` by
    the Ghostscript binary installed on the system.
    """
    LOGGER.info("Launch postscript watchdog...")

    init_directories(config["misc"]["output_path"], REQUIRED_DIRS)

    # gs_settings = config["misc"]["gs_settings"]
    event_handler = PostscriptEventHandler(
        gs_settings=None,
        ignore_directories=True
    )
    # Attach event handler to the configured output_path
    observer = InotifyObserver()
    observer.schedule(
        event_handler, config["misc"]["output_path"] + "ps/", recursive=False
    )
    observer.start()
    return observer


if __name__ == "__main__":  # pragma: no cover

    obs = setup_postscript_watchdog(
        {"misc": {"output_path": "./", "gs_settings": ["-sPAPERSIZE=b5", "-dFIXEDMEDIA"]}}
    )
    obs.join()
