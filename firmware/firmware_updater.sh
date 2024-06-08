#!/bin/bash
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

if [ $# -eq 0 ]; then
    echo "No arguments supplied; Expected udev fixed interface path (Ex: /dev/ttyACMX)." >&2
    exit 1
fi

if [ -L $1 ] ; then
    if [ -e $1 ] ; then
        # Good link: no-op
        :
    else
        # Link doesn't exist
        echo "<$1> doesn't exist !" >&2
        exit 1
    fi
elif [ -e $1 ] ; then
    echo "<$1> is not a symbolic link handled by udev; use it or use a manual flash" >&2
    echo "procedure (turn off services and flash the hardware with avrdude)." >&2
    exit 1
else
    echo "<$1> doesn't exist !" >&2
    exit 1
fi

# Inotify & avrdude will work only on the real hardware due to timmings constraints
# But we still need to totally disable systemd service during the flash,
# so we still need to get the fixed udev interface name.
real_hardware_device=$( basename "$( readlink -f "$1" )" )
interface_name=$(basename $1)
echo "Working on <$interface_name> -> <$real_hardware_device>"

echo "Stopping the service"
systemctl stop libre-printer@$interface_name.service
# Avoid restart from udev
systemctl mask libre-printer@$interface_name.service
sleep 2

echo "Restarting device..."
python ./restart_interface.py $1

retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error. Nothing done." >&2
    exit $retVal
fi

echo "Waiting for the device restart..."
inotifywait --timeout 4 --include "$real_hardware_device" --event create /dev/ >/dev/null || {
    (( $? == 2 ))  ## inotify exit status 2 means timeout expired
    echo "Unable to detect the interface!" >&2
    exit 1
}

echo "Flashing device..."
avrdude -v -patmega32u4 -cavr109 -P/dev/$real_hardware_device -b57600 -D -Uflash:w:./bin/libreprinter.ino.hex:i
sleep 7

echo "Restart the service"
systemctl unmask libre-printer@$interface_name.service
systemctl start libre-printer@$interface_name.service
