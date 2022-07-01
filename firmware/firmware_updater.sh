#!/bin/bash
#!/usr/bin/env python3
# Libreprinter is a software allowing to use the Centronics and serial printing
# functions of vintage computers on modern equipement through a tiny hardware
# interface.
# Copyright (C) 2020-2022  Ysard
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

if [ $# -eq 0 ]; then
    echo "No arguments supplied; Expected interface path."
fi

interface_name=$(basename $1)

echo "Stopping the service"
systemctl stop libre-printer@$interface_name.service

echo "Flashing device..."
./restart_interface.py $1

retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error. Nothing done."
    exit $retVal
fi

avrdude -v -patmega32u4 -cavr109 -P$1 -b57600 -D -Uflash:w:./firmware/libreprinter.ino.hex:i

echo "Restart the service"
systemctl start libre-printer@$interface_name.service
