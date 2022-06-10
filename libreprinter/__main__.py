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
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Libreprinter entry point"""
# Custom imports
from libreprinter import __version__
from libreprinter.config_parser import load_config
from libreprinter.file_handler import init_directories, cleanup_directories
from libreprinter.interface import read_interface
from libreprinter.jobs_to_printer_watchdog import setup_watchdog
from libreprinter.escp2_converter import launch_escp2_converter
import libreprinter.commons as cm

LOGGER = cm.logger()


def main():
    """The main routine."""
    LOGGER.info("Libreprinter start; %s", __version__)

    config = load_config()
    misc_section = config["misc"]

    # Reset output dirs
    if misc_section.getboolean("start_cleanup"):
        cleanup_directories(misc_section["output_path"])

    # Prepare working directories
    init_directories(misc_section["output_path"])

    # Launch converters
    converter_process = None
    if (misc_section["emulation"] in ("epson", "auto") and
        misc_section["endlesstext"] in ("strip-escp2-stream", "strip-escp2-jobs", "no")
    ):
        LOGGER.info("Launch convert-escp2 program...")
        converter_process = launch_escp2_converter(config)

    if (misc_section["output_printer"] != "no" and
        misc_section["endlesstext"] in ("plain-jobs", "strip-escp2-jobs", "no")
    ):
        # TODO: only "no" because strip wrongly builds empty pdf files
        # Send new pdfs and txt files on the printer configured in Cups
        # output_printer and not stream*:
        # output_printer is defined; it is not an infinite stream
        #  => send txt job to printer ("plain-jobs", "strip-escp2-jobs")
        #  => send pdf to printer ("no")
        setup_watchdog(config)

    # Launch interface reader
    read_interface(config)

    if converter_process:
        # Cleanup
        converter_process.kill()


if __name__ == "__main__":
    main()
