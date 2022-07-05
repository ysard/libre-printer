#  Libreprinter is a software allowing to use the Centronics and serial printing
#  functions of vintage computers on modern equipement through a tiny hardware
#  interface.
#  Copyright (C) 2020-2022  Ysard
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
"""Watchdog for /pcl directory that is able to convert new files into pdfs"""
# Standard imports
import shlex
from pathlib import Path
import subprocess
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import RegexMatchingEventHandler

# Custom imports
from libreprinter import plugins_handler
from libreprinter.commons import logger

LOGGER = logger()

CONFIG = {
    "misc": {
        "emulation": "hp",
        "endlesstext": "no",
    }
}


class PclEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class only reimplement :meth:`on_created` event.

    Watched directory:

        - `pcl`: `*.pcl`

    Attribute:
        :param converter_path: Path to GhostPCL binary.
        :type converter_path: str

    Class attribute:
        :param FILES_REGEX: Patterns to detect pcl files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*\.pcl$"]

    def __init__(self, *args, converter_path=None, **kwargs):
        """Constructor override
        Just add pcl_converter_path attr and define watchdog regexes.
        """
        super().__init__(*args, regexes=self.FILES_REGEX, **kwargs)
        self.converter_path = converter_path

    def on_closed(self, event):
        """PCL file creation is detected, convert it to PDF"""
        LOGGER.info("Event detected: %s", event)

        # Directly build arg list; enquote paths to avoid errors
        src_path = Path(event.src_path)
        pdf_path = src_path.parent / "../pdf" / (src_path.stem + ".pdf")
        args = [
            self.converter_path,
            "-dNOPAUSE", "-sDEVICE=pdfwrite", "-sColorConversionStrategy=RGB",
            f"-sOutputFile={shlex.quote(str(pdf_path))}",
            shlex.quote(event.src_path)
        ]
        try:
            # We are in a child thread, we can have blocking calls like run()
            # Capture all outputs from the command in case of error with PIPE
            subprocess.run(
                args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True
            )
        except subprocess.CalledProcessError as e:
            # process exits with a non-zero exit code
            LOGGER.error("stdout: %s; stderr: %s", e.stdout, e.stderr)
            LOGGER.exception(e)


@plugins_handler.register
def setup_pcl_watchdog(config):
    """Initialise a watchdog on `/pcl` directory in configured `output_path`.

    Any pcl file created in this directories will be converted in `/pdf` by
    the ghostpcl binary whose path is indicated in the variable
    `pcl_converter_path`.
    """
    LOGGER.info("Launch pcl watchdog...")

    # Test existence of pcl converter binary
    converter_path = config["misc"]["pcl_converter_path"]
    if not Path(converter_path).exists():
        LOGGER.error(
            "Setting <pcl_converter_path:%s> doesn't exists!", converter_path
        )
        raise FileNotFoundError("pcl converter not found")

    event_handler = PclEventHandler(
        converter_path=converter_path, ignore_directories=True
    )
    # Attach event handler to the configured output_path
    observer = InotifyObserver()
    observer.schedule(event_handler, config["misc"]["output_path"] + "pcl/", recursive=False)
    observer.start()


if __name__ == "__main__":  # pragma: no cover
    from libreprinter.commons import PCL_CONVERTER

    obs = setup_pcl_watchdog(
        {"misc": {"output_path": "./", "pcl_converter_path": PCL_CONVERTER}}
    )
    obs.join()
