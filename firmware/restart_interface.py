#!/usr/share/libre-printer/bin/python
#!/usr/bin/env python3
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
"""Script used to restart the Arduino interface
Note the shebang that uses the Python venv of the package

Usage:

    # Use /dev/ttyACM0 serial interface by default
    ./restart_interface.py

    # Use custom serial interface
    ./restart_interface.py "/dev/my_tty"
"""
import sys
from time import sleep
import serial


def touchForCDCReset(port="/dev/ttyACM0", *args, **kwargs):
    """Toggle 1200 bps on selected serial port to force board reset.

    See Arduino IDE implementation:
    https://github.com/arduino/Arduino/blob/master/arduino-core/src/processing/app/Serial.java
    https://github.com/arduino/Arduino/blob/master/arduino-core/src/cc/arduino/packages/uploaders/SerialUploader.java
    """
    serial_handler = serial.Serial(
        port=port,
        baudrate=1200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        dsrdtr=True,
    )
    assert serial_handler.is_open

    serial_handler.dtr=False
    serial_handler.close()

    # Scanning for available ports seems to open the port or
    # otherwise assert DTR, which would cancel the WDT reset if
    # it happened within 250 ms. So we wait until the reset should
    # have already occurred before we start scanning.
    sleep(0.250)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        touchForCDCReset()
        raise SystemExit
    touchForCDCReset(sys.argv[1])
