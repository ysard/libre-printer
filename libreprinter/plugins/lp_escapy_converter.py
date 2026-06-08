#  Libreprinter is a software allowing to use the Centronics and serial printing
#  functions of vintage computers on modern equipement through a tiny hardware
#  interface.
#  Copyright (C) 2020-2026  Ysard
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

Conversions are made thanks to Escapy.

As soon as a file is closed, a pdf is created.

Expected config:

    - misc: emulation + endlesstext: epson/auto + no
    - esc: preferred_backend: escapy
"""

# Standard imports
import configparser
from pathlib import Path
import subprocess
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import RegexMatchingEventHandler

# Custom imports
from libreprinter import plugins_handler
from libreprinter.file_handler import init_directories
from libreprinter.commons import logger, ESCAPY_BINARY

LOGGER = logger()

CONFIG = {
    "misc": {
        "emulation": ("epson", "auto"),
        "endlesstext": ("no",),
    },
    "esc": {"preferred_backend": "escapy"},
}
CHARACTERS_DB_DIR = "user_characters_db"  # Contain mappings.json
REQUIRED_DIRS = [CHARACTERS_DB_DIR]
SECTION_NAME = "escapy"


@plugins_handler.register_configurer
def configure_escapy(config: configparser.ConfigParser):
    """Check and set default configuration values for the current plugin

    :param config: Opened ConfigParser object
    """
    if SECTION_NAME not in config:
        config.add_section(SECTION_NAME)

    section = config[SECTION_NAME]

    if not section.get("escapy_path"):
        section["escapy_path"] = ESCAPY_BINARY

    if not section.get("config_file"):
        section["config_file"] = "/etc/escapy/escapy.conf"


class EscapyEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class only reimplements :meth:`on_closed` event.

    Watched directory:

        - `raw`: `*.raw`

    Attribute:
        :param settings: Escapy Section of the current ConfigParser.
        :type settings: configparser.SectionProxy | dict

    Class attribute:
        :param FILES_REGEX: Patterns to detect raw files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*\.raw$"]

    def __init__(self, settings: configparser.SectionProxy | dict, *args, **kwargs):
        """Constructor override
        Just set converter settings and define watchdog regexes.
        """
        super().__init__(*args, regexes=self.FILES_REGEX, **kwargs)
        self.settings = settings

    def build_command(self, src_path: Path):
        """Build argument list

        .. note:: Think about further support for:
            --pins
            --single_sheets, --no-single_sheets
        """
        pdf_path = src_path.parent.parent / "pdf" / (src_path.stem + ".pdf")
        characters_db = src_path.parent.parent / CHARACTERS_DB_DIR / "mappings.json"

        cmd = [
            self.settings["escapy_path"],
            str(src_path),
            "-db",
            str(characters_db),
            "-o",
            str(pdf_path),
        ]

        if "config_file" in self.settings:
            cmd.extend(["-c", self.settings["config_file"]])

        LOGGER.debug("escapy command: %s", cmd)
        return cmd

    def on_closed(self, event):
        """File closing is detected, convert it to PDF

        Minimal command::

            escapy ./raw/file.raw \
                -db user_characters_db/mappings.json \
                -o pdf/file.pdf \
                -c /etc/escapy/escapy.conf
        """
        LOGGER.info("Event detected: %s", event)

        cmd = self.build_command(Path(event.src_path))

        try:
            # We are in a child thread, we can have blocking calls like run()
            # Capture all outputs from the command in case of error with PIPE
            subprocess.run(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True
            )
        except subprocess.CalledProcessError as e:
            # process exits with a non-zero exit code
            LOGGER.error("stdout: %s; stderr: %s", e.stdout, e.stderr)
            LOGGER.exception(e)


@plugins_handler.register
def setup_escapy_watchdog(config: configparser.ConfigParser | dict):
    """Initialise a watchdog on `/raw` directory in configured `output_path`.

    Any raw file created in this directories will be converted in `/pdf` by
    the Escapy program installed on the system.
    """
    LOGGER.info("Launch escapy watchdog...")

    # Test existence of the binary
    escapy_path = config[SECTION_NAME]["escapy_path"]
    if not Path(escapy_path).exists():
        LOGGER.error("Setting <escapy_path:%s> doesn't exists!", escapy_path)
        raise FileNotFoundError("escapy converter not found")

    init_directories(config["misc"]["output_path"], REQUIRED_DIRS)

    event_handler = EscapyEventHandler(config[SECTION_NAME], ignore_directories=True)
    # Attach event handler to the configured output_path
    observer = InotifyObserver()
    observer.schedule(
        event_handler, config["misc"]["output_path"] + "raw/", recursive=False
    )
    observer.start()
    return observer


if __name__ == "__main__":  # pragma: no cover
    obs = setup_escapy_watchdog(
        {
            "misc": {
                "output_path": "./",
            },
            "escapy": {
                "escapy_path": ESCAPY_BINARY,
                "pins": "9",
                # "config_file": "my_config.conf",
            },
        }
    )
    obs.join()
