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
        misc_section["endlesstext"] in ("plain-jobs", "strip-escp2-jobs", "no")  # TODO: uniquement "no"
    ):
        # Send new pdfs and txt files on the printer configured in Cups
        # output_printer and not stream*:
        # output_printer is defined; it is not an infinite stream
        #  => send txt job to printer ("plain-jobs", "strip-escp2-jobs") # TODO: strip génère des PDFs vides...
        #  => send pdf to printer ("no")
        setup_watchdog(config)

    # Launch interface reader
    read_interface(config)

    if converter_process:
        # Cleanup
        converter_process.kill()


if __name__ == "__main__":
    main()
