"""Libreprinter entry point"""
# Custom imports
from libreprinter import __version__
from libreprinter.config_parser import load_config
from libreprinter.file_handler import init_directories
from libreprinter.interface import read_interface
from libreprinter.jobs_to_printer_watchdog import setup_watchdog
from libreprinter.escp2_converter import launch_escp2_converter
import libreprinter.commons as cm

LOGGER = cm.logger()


def main():
    """The main routine."""
    LOGGER.info("Libreprinter start; %s", __version__)

    config = load_config()

    # Prepare working directories
    init_directories(config["misc"]["output_path"])

    # Launch converters
    converter_process = None
    if (config["misc"]["emulation"] in ("epson", "auto") and
        config["misc"]["endlesstext"] in ("strip-escp2-stream", "strip-escp2-jobs", "no")
    ):
        LOGGER.info("Launch convert-escp2 program...")
        converter_process = launch_escp2_converter(config)

    if (config["misc"]["output_printer"] != "no" and
        config["misc"]["endlesstext"] in ("plain-jobs", "strip-escp2-jobs", "no")
    ):
        # Send new pdfs on the printer configured in Cups
        # output_printer is defined; it is not an infinite stream
        # output_printer and not stream*
        #  => send txt job to printer
        #  => send pdf to printer
        setup_watchdog(config)

    # Launch interface reader
    read_interface(config)

    if converter_process:
        # Cleanup
        converter_process.kill()


if __name__ == "__main__":
    main()
