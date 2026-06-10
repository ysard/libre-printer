# Libreprinter is a software allowing to use the Centronics and serial printing
# functions of vintage computers on modern equipement through a tiny hardware
# interface.
# Copyright (C) 2020-2024  Ysard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Open and use shared memory object created by converters"""

# Standard imports
import os
import mmap
from numpy import frombuffer, int32

# Custom imports
import libreprinter.commons as cm

SHARED_MEM_BUFFER = None
LOGGER = cm.logger()


def initialize_interprocess_com():
    """Init/open shared memory

    Shared file is at /dev/shm/retroprinter-shared-mem and initially created by
    converters.

    We just purpose a hacky r/w binding to this object (which is very badly
    implemented in converters: the original project hopes to store a packet
    based on int16 into 2 int8 in 2 separated bytes in shared memory.
    In fact the OS uses 4 bytes (int32) for each "int" stored. So, for 512 packets
    we use 2048 bytes, and by accessing to 405 offset we access to 1620 offset in file.
    The file is badly initialized but it works because the OS reserves much more
    data than 512 bytes: a multiple of page size.).

    .. note:: Equivalent of legacy "initialize_interface_comms"

    :return: The file handler on the shared memory file for its proper closing.
    :rtype: <_io.BufferedRandom>
    """
    global SHARED_MEM_BUFFER

    shared_mem_path = "/dev/shm/" + cm.SHARED_MEM_NAME
    shared_mem_size = 512 * 4

    if not os.path.isfile(shared_mem_path):
        # Create not existing file
        os.mknod(shared_mem_path)  # Will work only on Unix => who cares?

    # Truncate the file to the expected size in all cases
    # Without this, we can't access to all memory used by buggy converters
    # (limited to the 512 first bytes).
    os.truncate(shared_mem_path, shared_mem_size)

    f_d = open(shared_mem_path, mode="rb+")
    m = mmap.mmap(f_d.fileno(), length=0, access=mmap.ACCESS_WRITE)

    SHARED_MEM_BUFFER = frombuffer(m, dtype=int32)

    LOGGER.debug("Shared mem initialised")
    # print(SHARED_MEM_BUFFER[400:405])
    debug_shared_memory()
    return f_d


def get_status_message(offset):
    """Get value at the given address in shared memory

    Expects that :meth:`initialize_interprocess_com` is called before.

    .. note:: Equivalent of legacy "peekPacketWord"

    :rtype: int
    """
    global SHARED_MEM_BUFFER

    offset *= 2
    return SHARED_MEM_BUFFER[offset + 1]


def send_status_message(offset, value):
    """Put given value to the given offset in shared memory

    Expects that :meth:`initialize_interprocess_com` is called before.

    .. note:: Equivalent of legacy "pokePacketWord"

    :param offset: Address
    :param value: Value
    :type offset: int
    :type value: int
    """
    global SHARED_MEM_BUFFER

    offset = offset * 2
    SHARED_MEM_BUFFER[offset + 1] = value


def debug_shared_memory():
    """Display content of status messages in shared memory

    .. note:: Pending jobs are not showed.
    """
    words_table = {
        200: {
            0: "Can't control",
            1: "Conversion program is in control",
            2: "Capture program is in control",
        },
        201: {
            0: "waiting data: convertor finished",
            1: "processing data: convertor running",
        },
        202: {
            0: "no data to process or data is processed",
            1: "data to process",
            3: "end of job forced",
        },
    }

    # Get 202 message: at offset 200 * 2 + 1 = 401
    value = get_status_message(200)
    print(
        "200: Power Led control and unlock buggy converters:",
        value,
        words_table[200][value],
    )
    # Get 202 message: at offset 201 * 2 + 1 = 403
    value = get_status_message(201)
    print(
        "201: Converters to convert-flasher:", value, words_table[201][value]
    )  # TODO convert-flasher uniquement ???
    # Get 202 message: at offset 202 * 2 + 1 = 405
    value = get_status_message(202)
    print("202: Interface to converters raw/escp2:", value, words_table[202][value])
