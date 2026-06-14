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
"""Classes that define the internal API between the engine that manages the
interface, the files, and the plugins that process data on the fly.

Data processors must never manipulate files directly.

Processors communicate with the core application exclusively through Command
objects emitted by process_chunk() and the other lifecycle hooks.
"""

# Standard imports
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import configparser
    from typing import Generator


class DataProcessor:
    """Base class for data stream processing plugins.

    A data processor receives chunks of bytes coming from the communication
    interface and emits commands describing theactions to perform.

    Subclasses may transform incoming data, split jobs, trigger exports
    or request synchronization of external converters.

    The plugin should generally not manipulate file handles
    or be aware of their locations.

    The processing lifecycle is:

        start_job()
            Called when a new job begins.

        process_chunk()
            Called for each received data block.

        end_job()
            Called when the current job ends.

        post_process()
            Called after the job has been fully written and closed.
    """

    def __init__(self, config: configparser.ConfigParser):
        """Initialise the processor with the application configuration"""
        self.config = config

    def start_job(self, job_number: int):
        """Prepare processing of a new job

        :param job_number: Identifier assigned to the incoming job.
        """

    def process_chunk(self, databytes: bytearray) -> Generator:
        """Process a received block of bytes

        Subclasses should yield one or more Command instances.

        :param databytes: Raw bytes received from the interface.
        """
        yield WriteChunk(databytes)

    def end_job(self):
        """Finalise processing of the current job

        Called immediately before the job file is closed.
        """

    def post_process(self, job_number: int):
        """Perform actions after a job has been written.

        This hook is typically used to request exports or launch
        external processing steps.

        :param job_number: Identifier of the completed job.
        """


@dataclass
class WriteChunk:
    """Write raw bytes to the current job file

    This is the default command emitted by data processors.
    The payload is appended to the currently opened output file.
    """

    data: bytearray


@dataclass
class RotateJob:
    """Close the current job and start a new one

    This command is typically emitted when a processor detects
    a protocol-specific boundary between two jobs within the
    same incoming data stream.
    """
