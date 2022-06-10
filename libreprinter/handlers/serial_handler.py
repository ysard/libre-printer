# Libreprinter is a software allowing to use the Centronics and serial printing
# functions of vintage computers on modern equipement through a tiny hardware
# interface.
# Copyright (C) 2020-2021  Ysard
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
# Standard imports
import os
import time
import serial

# Custom imports
from libreprinter.commons import BAUDRATE
from libreprinter.commons import logger

LOGGER = logger()


def _get_serial_handler(serial_path):
    """Open serial port and return serial handler

    Low level function, prefer using :meth:get_serial_handler.

    TODO: reset DTR => ok ? marche pas tout le temps
    TODO: DTR on Rpi ? => gpio control
    TODO: flush buffer after open

    .. note:: doc: See rtscts=True and dsrdtr=True
        https://github.com/pyserial/pyserial/issues/59

    :return: Serial port handler.
    :rtype: serial.Serial
    """
    if not os.path.exists(serial_path):
        LOGGER.error("Serial port <%s> not available!", serial_path)
        return

    # Configure first and open later: allow to assert DTR line during opening
    # PS: Opened mode: os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK
    serial_handler = serial.Serial()
    serial_handler.port = serial_path
    serial_handler.baudrate = BAUDRATE
    serial_handler.timeout = 1
    # Reset Arduino
    # TODO: True or false works for a reset :o
    # deassert the DTR line is also working ? it should forbid the reboot of arduino ?
    serial_handler.dtr = True
    try:
        serial_handler.open()
        assert serial_handler.is_open
        serial_handler.dtr = False  # This line raises an exception on emulated interface
        time.sleep(1)
        assert serial_handler.is_open

    except serial.serialutil.SerialException as e:
        LOGGER.exception(e)
        return

    # Wait Arduino boot after DTR signal
    time.sleep(1)
    # Flush not expected random input data...
    serial_handler.reset_input_buffer()
    return serial_handler


def get_serial_handler(serial_path):
    """Try to open serial port and return serial handler

    :return: Serial port handler. Test it 5 times until return None.
    :rtype: serial.Serial
    """
    error = 0
    while error < 5:
        serial_handler = _get_serial_handler(serial_path)
        if serial_handler:
            return serial_handler
        error += 1
        time.sleep(1)
