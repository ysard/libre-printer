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
# Standard imports
import argparse
from pathlib import Path

# Custom imports
from libreprinter import __version__
from libreprinter import plugins
from libreprinter.config_parser import load_config
from libreprinter.file_handler import init_directories, cleanup_directories
from libreprinter.interface import read_interface
import libreprinter.commons as cm

LOGGER = cm.logger()


def libreprinter_entry_point(config_file=None, *args, **kwargs):
    """The main routine."""
    LOGGER.info("Libreprinter start; %s", __version__)

    config = load_config(config_file=config_file)
    misc_section = config["misc"]

    # Reset output dirs
    if misc_section.getboolean("start_cleanup"):
        cleanup_directories(misc_section["output_path"])

    # Prepare working directories
    init_directories(misc_section["output_path"])

    # Launch converters & watchdogs
    plugins_loaded = plugins.plugins(config)
    process_to_kill = [
        plugins.get_functions(plugin)(config) for plugin in plugins_loaded
    ]

    # Launch interface reader
    read_interface(config)

    # Cleanup processes
    [
        converter_process.kill()
        for converter_process in process_to_kill
        if converter_process
    ]


def args_to_params(args):
    """Return argparse namespace as a dict {variable name: value}"""
    return dict(vars(args).items())


def main():
    """Entry point and argument parser"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-C",
        "--config_file",
        nargs="?",
        help="Configuration file to use.",
        default=cm.CONFIG_FILE,
        type=Path,
    )

    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )

    # Get program args and launch associated command
    args = parser.parse_args()

    params = args_to_params(args)
    # Quick check
    assert params["config_file"].exists(), \
        f"Configuration file <{params['config_file']}> not found!"

    # Do magic
    libreprinter_entry_point(**params)


if __name__ == "__main__":
    main()
