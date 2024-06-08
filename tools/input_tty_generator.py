#!/usr/bin/env python3
"""Script used to send a binary file to a virtual tty linked opened by the Libre-Printer service

Usage:

    $ ./input_tty_generator.py my_file.prn

Note: By default it will use the following file used for tests:
`test_data/escp2_1.prn`

"""
import sys


def write_tty(prn_file):
    """Write the given file content to the virtual tty ./input-tty initialized with socat"""
    with open(prn_file, "rb") as f_d, open("./input-tty", "wb") as tty_d:
        # Dump per line
        for i in f_d:
            tty_d.write(i)

        # Dump per byte (less efficient)
        # byte = f_d.read(1)
        #
        # while byte:
        #     # print(byte)
        #     tty_d.write(byte)
        #
        #     byte = f_d.read(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file = sys.argv[1]
    else:
        file = "../test_data/escp2_1.prn"

    print("File opened: ", file)
    write_tty(file)
