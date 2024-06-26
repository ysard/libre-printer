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
"""Logger settings and project constants"""

# Standard imports
from logging.handlers import RotatingFileHandler
import logging
import datetime as dt
import tempfile
import os


# Misc
BAUDRATE = 500000  # Yolo, it's USB CDC
OUTPUT_DIRS = ("raw", "pcl", "png", "pdf", "txt_stream")
DEFAULT_OUTPUT_PATH = os.getcwd()
SHARED_MEM_NAME = "retroprinter-shared-mem"
LAST_HARDWARE_VERSION = "1.0.0.rc1"

# Paths
DIR_LOGS = tempfile.gettempdir() + "/"
CONFIG_FILE = "./libreprinter.conf"
ESCP2_CONVERTER = "/home/pi/temp/sdl/escparser/convert-escp2"
PCL_CONVERTER = "/usr/local/bin/gpcl6"
ENSCRIPT_BINARY = "/usr/bin/enscript"
HP2XX_BINARY = "/usr/bin/hp2xx"

REPORT_BUG_URL = "https://github.com/ysard/libre-printer/issues/new"

# Logging
LOGGER_NAME = "libreprinter"
LOG_LEVEL = "INFO"

################################################################################


def logger(name=LOGGER_NAME):
    """Return logger of given name, without initialize it.

    Equivalent of logging.getLogger() call.
    """
    logger_obj = logging.getLogger(name)
    fmt_str = "%(levelname)s: [%(filename)s:%(lineno)s:%(funcName)s()] %(message)s"
    logging.basicConfig(format=fmt_str)
    return logger_obj


_logger = logging.getLogger(LOGGER_NAME)
_logger.setLevel(LOG_LEVEL)

# log file
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: [%(filename)s:%(lineno)s:%(funcName)s()] :: %(message)s"
)
file_handler = RotatingFileHandler(
    DIR_LOGS
    + LOGGER_NAME
    + "_"
    + dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    + ".log",
    "a",
    100_000_000,
    1,
)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)
_logger.addHandler(file_handler)

# terminal log
# stream_handler = logging.StreamHandler()
# formatter = logging.Formatter("%(levelname)s: %(message)s")
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(LOG_LEVEL)
# _logger.addHandler(stream_handler)


def log_level(level):
    """Set terminal/file log level to the given one.

    .. note:: Don't forget the propagation system of messages:
        From logger to handlers. Handlers receive log messages only if
        the main logger doesn't filter them.
    """
    level = level.upper()
    if level == "NONE":
        logging.disable()
        return
    # Main logger
    _logger.setLevel(level)
    # Handlers
    [
        handler.setLevel(level)
        for handler in _logger.handlers
        if handler.__class__
        in (logging.StreamHandler, logging.handlers.RotatingFileHandler)
    ]
