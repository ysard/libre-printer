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
"""Watchdog for /raw directory that is able to parse & convert new files
into CSV and/or into pdfs

Conversions are made thanks to Seiko-converter.

As soon as a raw file is modified or closed, a pdf is created.
This allows to always have the latest data available even with long gate modes
configured on the QT-2100 device.
"""

# Standard imports
from importlib.util import find_spec
from pathlib import Path
from datetime import datetime
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import RegexMatchingEventHandler, FileSystemEvent

# Custom imports
from libreprinter import plugins_handler
from libreprinter.commons import logger

LOGGER = logger()

CONFIG = {
    "misc": {
        "emulation": "seiko-qt2100",
    }
}


class SeikoEventHandler(RegexMatchingEventHandler):
    """Watch a directory via a parent Observer and emit events accordingly

    This class reimplements :meth:`on_created` + :meth:`on_closed` events.

    Watched directory:

        - `raw`: `*.raw`

    Attributes:
        :param seiko_settings: Settings of the seiko-qt2100 section from the config file.
        :param last_timestamp: Keep the timestamp of the last modified file event.
            Used to reduce overhead.
        :type seiko_settings: dict
        :type last_timestamp: float

    Class attribute:
        :param FILES_REGEX: Patterns to detect files.
        :type FILES_REGEX: list[str]
    """

    FILES_REGEX = [r".*\.raw"]

    def __init__(self, *args, seiko_settings=None, **kwargs):
        """Constructor override
        Just add converter settings attr and define watchdog regexes.
        """
        super().__init__(*args, regexes=self.FILES_REGEX, **kwargs)
        self.seiko_settings = seiko_settings
        self.last_timestamp = datetime.now().timestamp()

    def on_modified(self, event: FileSystemEvent) -> None:
        """File is modified, generate partial files"""
        timestamp = datetime.now().timestamp()
        if timestamp - self.last_timestamp > 4:
            self.last_timestamp = timestamp
            self.build_data(event)

    def on_closed(self, event):
        """File creation is detected, generate full files"""
        self.build_data(event)

    def build_data(self, event):
        """Generate csv and/or pdf files according to the config file specs"""
        from seiko_converter.qt2100_parser import SeikoQT2100Parser
        from seiko_converter.qt2100_converter import SeikoQT2100GraphTool

        LOGGER.debug("Event detected: %s", event)
        src_path = Path(event.src_path)
        out_path = str(src_path.parent / "../{0}" / (src_path.stem + ".{0}"))

        parser = SeikoQT2100Parser(src_path)
        obj = SeikoQT2100GraphTool(parser)
        if self.seiko_settings["enable-csv"]:
            obj.to_csv(output_filename=out_path.format("csv"))
        if self.seiko_settings["enable-graph"]:
            obj.to_graph(output_filename=out_path.format("pdf"), **self.seiko_settings)


@plugins_handler.register
def setup_seiko_watchdog(config):
    """Initialise a watchdog on `/raw` directory in configured `output_path`.

    Any raw file created in this directory will be converted in `/pdf` or `/csv`
    by the seiko-converter Python program installed on the system.
    """
    LOGGER.info("Launch seiko watchdog...")

    # Test the existence of the external module
    if find_spec("seiko_converter") is None:
        LOGGER.error("<seiko_converter> module is not installed!")
        return

    # Format values from the config files (especially the cutoff numeric value)
    temp_config = dict()
    for key in config["seiko-qt2100"].keys():
        try:
            temp_config[key] = config["seiko-qt2100"].getboolean(key, True)
        except ValueError:
            temp_config[key] = config["seiko-qt2100"].getfloat(key)

    print(temp_config)
    event_handler = SeikoEventHandler(
        seiko_settings=temp_config, ignore_directories=True
    )
    # Attach event handler to the configured output_path
    observer = InotifyObserver()
    observer.schedule(
        event_handler, config["misc"]["output_path"] + "raw/", recursive=False
    )
    observer.start()
    return observer


if __name__ == "__main__":  # pragma: no cover
    obs = setup_seiko_watchdog(
        {
            "misc": {"output_path": "./"},
            "seiko-qt2100": {"enable-csv": True, "enable-graph": True},
        }
    )
    obs.join()
