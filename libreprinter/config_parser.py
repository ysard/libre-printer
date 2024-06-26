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
"""Load configuration file, check and set default values"""
# Standard imports
import configparser

# Custom imports
from libreprinter.commons import logger, log_level, CONFIG_FILE, ESCP2_CONVERTER, \
    PCL_CONVERTER, ENSCRIPT_BINARY, DEFAULT_OUTPUT_PATH, LOG_LEVEL

FLOW_CTRL_MAPPING = {
    "hardware": 1,
    "software": 2,
    "both": 3,
}

LOGGER = logger()


def load_config(config_file=CONFIG_FILE):
    """Load configuration file and set default settings

    :param config_file: Path of the configuration file to load.
        Default: CONFIG_FILE from commons module.
    :type config_file: Path
    :return: Configuration updated object.
    :rtype: configparser.ConfigParser
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    return parse_config(config)


def parse_config(config: configparser.ConfigParser):
    """Read config file, check and set default values

    .. note:: All values are of type string; they must be casted
        (with dedicated methods) if necessary.

        The syntax `if not xxx:` handles None and '' data retrieved from file.

    :param config: Opened ConfigParser object
    :type config: configparser.ConfigParser
    :return: Processed ConfigParser object
    :rtype: configparser.ConfigParser
    """
    # rb = parser.getint('section', 'rb') if parser.has_option('section', 'rb') else None

    ## Misc section
    misc_section = config["misc"]
    loglevel = misc_section.get("loglevel")
    if not loglevel:
        misc_section["loglevel"] = LOG_LEVEL
    log_level(misc_section["loglevel"])

    start_cleanup = misc_section.get("start_cleanup")
    if not start_cleanup:
        misc_section["start_cleanup"] = "no"

    escp2_converter_path = misc_section.get("escp2_converter_path")
    if not escp2_converter_path:
        misc_section["escp2_converter_path"] = ESCP2_CONVERTER

    pcl_converter_path = misc_section.get("pcl_converter_path")
    if not pcl_converter_path:
        misc_section["pcl_converter_path"] = PCL_CONVERTER

    enscript_path = misc_section.get("enscript_path")
    if not enscript_path:
        misc_section["enscript_path"] = ENSCRIPT_BINARY

    enscript_settings = misc_section.get("enscript_settings")
    if not enscript_settings:
        config["misc"]["enscript_settings"] = "-BR"

    if misc_section.get("endlesstext") not in (
        "plain-stream", "strip-escp2-stream", "plain-jobs", "strip-escp2-jobs"
    ):
        misc_section["endlesstext"] = "no"

    line_ending = misc_section.get("line_ending")
    if line_ending == "windows":
        misc_section["line_ending"] = "\r\n"
    else:
        # unix
        misc_section["line_ending"] = "\n"

    # Warning: If usb_passthrough is set, output_printer is not disabled.
    # It should be noted that any "raw" parallel interface like `/dev/usb/lpx`
    # disappears when Cups is used on it. Thus it can't be used with this
    # functionality anymore.
    usb_passthrough = misc_section.get("usb_passthrough")
    if not usb_passthrough:
        misc_section["usb_passthrough"] = "no"

    output_printer = misc_section.get("output_printer")
    if not output_printer:
        misc_section["output_printer"] = "no"

    # Disable output_printer if data from host is streamed continuously
    if "stream" in misc_section["endlesstext"]:
        misc_section["output_printer"] = "no"

    serial_port = misc_section.get("serial_port")
    if not serial_port:
        misc_section["serial_port"] = "/dev/ttyACM0"

    if misc_section.get("emulation") not in ("epson", "escp2", "hp", "pcl", "text"):
        misc_section["emulation"] = "auto"
    if misc_section.get("emulation") in ("hp", "pcl"):
        misc_section["emulation"] = "hp"
    if misc_section.get("emulation") in ("epson", "escp2"):
        misc_section["emulation"] = "epson"

    output_path = misc_section.get("output_path", DEFAULT_OUTPUT_PATH)
    output_path = output_path or DEFAULT_OUTPUT_PATH
    output_path = output_path + "/" if output_path[-1] != "/" else output_path
    misc_section["output_path"] = output_path

    auto_end_page = misc_section.get("auto_end_page")
    if not auto_end_page:
        misc_section["auto_end_page"] = "no"

    end_page_timeout = misc_section.get("end_page_timeout")
    if (
        not end_page_timeout
        or not end_page_timeout.isnumeric()
        or int(end_page_timeout) <= 0.6
    ):
        if end_page_timeout and int(end_page_timeout) <= 0.6:
            LOGGER.warning(
                "User defined a very small end_page_timeout (≤0.6) for serial "
                "reception!\n"
                "The interface will not have enough time to empty its buffer. "
                "Setting will be defined to 2."
            )
        # Not able to detect end of page with a 0 timeout
        misc_section["end_page_timeout"] = "2"

    retain_data = misc_section.get("retain_data")
    if not retain_data:
        misc_section["retain_data"] = "yes"

    ## Parallel printer
    parallel_section = config["parallel_printer"]

    delayprinter = parallel_section.get("delayprinter")
    if (delayprinter is None) or (not delayprinter.isnumeric()):
        parallel_section["delayprinter"] = "0"

    ## Serial printer
    serial_section = config["serial_printer"]

    dtr_logic = serial_section.get("dtr_logic")
    if dtr_logic not in ("high", "low"):
        serial_section["dtr_logic"] = "high"

    enabled = serial_section.get("enabled")
    if enabled not in ("yes", "no", "auto"):
        serial_section["enabled"] = "no"

    baudrate = serial_section.get("baudrate")
    if not baudrate or not baudrate.isnumeric():
        serial_section["baudrate"] = "19200"
    elif int(baudrate) > 19200:  # pragma: no cover
        LOGGER.warning(
            "User defined high baudrate (>19200) for serial reception!\n"
            "This may be higher than the value the host configuration can support. "
            "You have been warned :p"
        )

    flow_control = serial_section.get("flow_control")
    if flow_control not in ("hardware", "software", "both"):
        serial_section["flow_control"] = "hardware"

    debug_config_file(config)
    return config


def debug_config_file(config: configparser.ConfigParser):
    """Display sections, keys and values of config file

    :param config: Opened ConfigParser object
    :type config: configparser.ConfigParser
    """
    for section in config.sections():
        LOGGER.debug("[%s]", section)

        for key, value in config[section].items():
            LOGGER.debug("%s : %s", key, value)

        LOGGER.debug("")
