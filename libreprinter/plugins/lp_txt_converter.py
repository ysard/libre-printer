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
"""Watchdog for /txt_jobs directory that is able to convert new files into pdfs

Conversions are made thanks to Enscript & Ghostscript.

As soon as a txt file is created, a pdf is created.

Expected config (emulation + endlesstext):

    - epson + plain-jobs
    - epson + strip-escp2-jobs
    - text + no

Yes the following config targets also: `epson + no`, `text + plain-jobs`
but in the first case there will be no text file, and in the 2nd case there
will be a text file due to `text` (`plain-jobs` is only for epson emulations).

So... The plugin is not compatible with `hp` emulation,
nor with `*stream` in endlesstext setting.
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
        "emulation": ("text", "epson"),
        "endlesstext": ("no", "plain-jobs", "strip-escp2-jobs"),
    }
}
REQUIRED_DIRS = ["txt_jobs"]


class TxtEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class only reimplement :meth:`on_closed` event.

    Watched directory:

        - `txt_jobs`: `*.txt`

    Attributes:
        :param enscript_path: Path of the Enscript binary from the config file.
        :param enscript_settings: Command line settings for Enscript binary.
        :type enscript_path: str
        :type enscript_settings: str

    Class attribute:
        :param FILES_REGEX: Patterns to detect txt files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*\.txt$"]

    def __init__(self, *args, enscript_path=None, enscript_settings=None, **kwargs):
        """Constructor override
        Just add Enscript settings attr and define watchdog regexes.
        """
        super().__init__(*args, regexes=self.FILES_REGEX, **kwargs)
        self.enscript_path = enscript_path
        self.enscript_settings = enscript_settings

    def on_closed(self, event):
        """File closing is detected, convert it to PDF

        Minimal command::

            enscript -R -p - input_tty_generator.py | gs -sDEVICE=pdfwrite -o out.pdf -
        """
        LOGGER.info("Event detected: %s", event)

        # Directly build arg list; enquote paths to avoid errors
        src_path = Path(event.src_path)
        pdf_path = src_path.parent / "../pdf" / (src_path.stem + ".pdf")
        enscript_cmd = [
            self.enscript_path,
            self.enscript_settings,
            "-p",
            "-",
            shlex.quote(event.src_path),
        ]
        ghostscript_cmd = [
            "/usr/bin/gs",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-sColorConversionStrategy=RGB",
            "-dCompatibilityLevel=1.7",  # Fix for reproductibility
            "-dEmbedAllFonts=true",  # Increase the final size
            "-dSubsetFonts=true",  # Reduce the final size
            f"-sOutputFile={shlex.quote(str(pdf_path))}",
            "-",
        ]
        LOGGER.debug("enscript command: %s", enscript_cmd)
        LOGGER.debug("ghostscript command: %s", ghostscript_cmd)
        try:
            # We are in a child thread, we can have blocking calls like run()
            # Capture all outputs from the command in case of error with PIPE
            ps = subprocess.Popen(enscript_cmd, stdout=subprocess.PIPE)
            ps.wait()
            subprocess.check_output(ghostscript_cmd, stdin=ps.stdout)
        except subprocess.CalledProcessError as e:
            # process exits with a non-zero exit code
            LOGGER.error("stdout: %s; stderr: %s", e.stdout, e.stderr)
            LOGGER.exception(e)


@plugins_handler.register
def setup_text_watchdog(config):
    """Initialise a watchdog on `/txt_jobs` directory in configured `output_path`.

    Any txt file created in this directories will be converted in `/pdf` by
    the Enscript & Ghostscript binaries installed on the system.
    """
    LOGGER.info("Launch text watchdog...")

    # Test existence of Enscript binary
    enscript_path = config["misc"]["enscript_path"]
    if not Path(enscript_path).exists():
        LOGGER.error("Setting <enscript_path:%s> doesn't exists!", enscript_path)
        raise FileNotFoundError("enscript converter not found")

    init_directories(config["misc"]["output_path"], REQUIRED_DIRS)

    enscript_settings = config["misc"]["enscript_settings"]
    event_handler = TxtEventHandler(
        enscript_path=enscript_path,
        enscript_settings=enscript_settings,
        ignore_directories=True
    )
    # Attach event handler to the configured output_path
    observer = InotifyObserver()
    observer.schedule(
        event_handler, config["misc"]["output_path"] + "txt_jobs/", recursive=False
    )
    observer.start()
    return observer


if __name__ == "__main__":  # pragma: no cover

    obs = setup_text_watchdog(
        {"misc": {"output_path": "./", "enscript_path": "/usr/bin/enscript", "enscript_settings": "-2Gr"}}
    )
    obs.join()
