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
"""Watchdog for /hpgl directory that is able to convert new files into pdfs

Conversions are made thanks to Hp2xx & Ghostscript.

As soon as a hpgl file is created, a pdf is created.

Expected config (emulation + endlesstext):

    - hpgl + no
"""
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
        "emulation": ("hpgl",),
        "endlesstext": ("no",),
    }
}


class HpglEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class only reimplement :meth:`on_created` event.

    Watched directory:

        - `hpgl`: `*.hpgl`

    Attribute:
        :param hp2xx_settings: Command line settings for Hp2xx binary.
        :type hp2xx_settings: str

    Class attribute:
        :param FILES_REGEX: Patterns to detect txt files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*\.hpgl$"]

    def __init__(self, *args, hp2xx_path=None, hp2xx_settings=None, **kwargs):
        """Constructor override
        Just add Hp2xx settings attr and define watchdog regexes.
        """
        super().__init__(*args, regexes=self.FILES_REGEX, **kwargs)
        self.hp2xx_path = hp2xx_path
        self.hp2xx_settings = hp2xx_settings

    def on_closed(self, event):
        """File creation is detected, convert it to PDF

        Minimal command::

            hp2xx -m eps -q -t -f out.ps in.hpgl
        """
        LOGGER.info("Event detected: %s", event)

        # Directly build arg list; enquote paths to avoid errors
        src_path = Path(event.src_path)
        pdf_path = src_path.parent / "../pdf" / (src_path.stem + ".pdf")
        args = [
            self.hp2xx_path,
            "-m", "eps",  # PostScript output
            "-q",
            "-t",
            "-f-"
        ]
        args += self.hp2xx_settings.split() if self.hp2xx_settings else []
        args.append(shlex.quote(event.src_path))

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
        LOGGER.debug("hp2xx command: %s", args)

        try:
            # We are in a child thread, we can have blocking calls like run()
            # Capture all outputs from the command in case of error with PIPE
            ps = subprocess.Popen(args, stdout=subprocess.PIPE)
            ps.wait()

            # Extract Bounding Box in 1/72 inch values
            stdout = ps.stdout.read()
            header_lines = stdout[:400].split(b"\n")
            width = height = ""
            if len(header_lines) >= 6 and b"BoundingBox" in header_lines[5]:
                # Extract the 2 last values
                width, height = map(int, header_lines[5].decode().split()[-2:])
            if width:
                # Insert the values in the GhostScript command
                ghostscript_cmd = ghostscript_cmd[:-1] + [
                    f"-dDEVICEWIDTHPOINTS={width}",
                    f"-dDEVICEHEIGHTPOINTS={height}",
                    "-",
                ]

            LOGGER.debug("ghostscript command: %s", ghostscript_cmd)
            ps = subprocess.Popen(ghostscript_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout_data, stderr_data = ps.communicate(input=stdout)
            if stderr_data:
                LOGGER.error(stderr_data)
        except subprocess.CalledProcessError as e:
            # process exits with a non-zero exit code
            LOGGER.error("stdout: %s; stderr: %s", e.stdout, e.stderr)
            LOGGER.exception(e)


@plugins_handler.register
def setup_hpgl_watchdog(config):
    """Initialise a watchdog on `/hpgl` directory in configured `output_path`.

    Any hpgl file created in this directories will be converted in `/pdf` by
    the Hp2xx & Ghostscript binaries installed on the system.
    """
    LOGGER.info("Launch hpgl watchdog...")

    # Test existence of the binary
    hp2xx_path = config["misc"]["hp2xx_path"]
    if not Path(hp2xx_path).exists():
        LOGGER.error("Setting <hp2xx_path:%s> doesn't exists!", hp2xx_path)
        raise FileNotFoundError("hp2xx_path converter not found")

    # hp2xx_settings = config["misc"]["hp2xx_settings"]
    event_handler = HpglEventHandler(
        hp2xx_path=hp2xx_path, hp2xx_settings=None, ignore_directories=True
    )
    # Attach event handler to the configured output_path
    observer = InotifyObserver()
    observer.schedule(
        event_handler, config["misc"]["output_path"] + "hpgl/", recursive=False
    )
    observer.start()
    return observer


if __name__ == "__main__":  # pragma: no cover
    obs = setup_hpgl_watchdog(
        {
            "misc": {
                "output_path": "./",
                "hp2xx_path": "/usr/bin/hp2xx",
                "hp2xx_settings": None,
            }
        }
    )
    obs.join()
