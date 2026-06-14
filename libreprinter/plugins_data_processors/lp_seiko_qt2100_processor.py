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
"""Seiko qt2100 timegrapher data processor

Is enabled only if the emulation `seiko-qt2100` is selected.
"""

# Standard imports
import struct
from datetime import datetime
from typing import TYPE_CHECKING

# Custom imports
from libreprinter import plugins_handler
from libreprinter.plugin_commands import DataProcessor, WriteChunk, RotateJob
from libreprinter.commons import logger

if TYPE_CHECKING:
    import configparser
    from typing import Generator


LOGGER = logger()

CONFIG = {
    "misc": {
        "emulation": "seiko-qt2100",
    }
}


@plugins_handler.register
class SeikoProcessor(DataProcessor):
    """Seiko qt2100 timegrapher data processor"""

    def __init__(self, config: configparser.ConfigParser):
        """Initialise the processor"""
        super().__init__(config)
        # Seiko qt2100 control
        self.job_timestamp = None
        self.probe_seiko = False
        self.escmode = False

    def process_chunk(self, databytes) -> Generator:
        """On-the-fly processing of data from the timegrapher

        Add timestamp before each new values in an ESC T message
        AND cut a stream with multiple successive data analysis

        :param databytes: Incoming raw data
        """
        edited_databytes = bytearray()
        for databyte in databytes:
            if databyte == 27:
                self.escmode = True
            elif self.escmode and databyte == ord("0"):
                if self.probe_seiko:
                    # At least a second data stream is received
                    # Dump the end of the previous one
                    yield WriteChunk(edited_databytes[:-1])

                    # Hijack the normal execution flow by creating a new file
                    # without having to return to the read_interface function
                    yield RotateJob()

                    # Keep the start of the next one
                    edited_databytes = edited_databytes[-1:]

                self.job_timestamp = None
                self.probe_seiko = True
            elif self.escmode and databyte == ord("1"):
                if not self.job_timestamp:
                    # First ESC sequence seen
                    # Initialise a job start timestamp
                    self.job_timestamp = datetime.now()
                    delta = 0
                else:
                    delta = (datetime.now() - self.job_timestamp).seconds
                # Note: Difference with the Retroprinter implementation!
                # We prefix ALL values with a delta, including the first one
                # (with a delta of 0 for this one)
                hours, minutes, seconds = (
                    (delta // 3600) & 0xFF,
                    delta % 3600 // 60,
                    delta % 60,
                )
                timestamp = struct.pack("BBB", hours, minutes, seconds)
                # Insert timestamp
                edited_databytes += b"T" + timestamp + b"\x1b"
            else:
                self.escmode = False

            edited_databytes += databyte.to_bytes(1)

        yield WriteChunk(edited_databytes)
