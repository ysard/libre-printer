"""Parametrize and launch espc2 converter as subprocess"""
# Standard imports
import shlex
import subprocess
import pathlib
# Custom imports
import libreprinter.commons as cm

LOGGER = cm.logger()


ENDLESS_TEXT_VALUE_MAPPING = {
    "no": 0,
    "plain-stream": 1,
    "strip-escp2-stream": 2,
    "plain-jobs": 3,
    "strip-escp2-jobs": 4,
}
# Doc of options in legacy project:
# NO_PLAIN_TEXT       0  # Do not create .txt files
# STREAM_PLAIN_TEXT   1  # Stream all incoming data to a single 1.txt file
# STREAM_STRIP_ESCP2  2  # Stream all incoming data to a single 1.txt file but strip out ESC/P2 codes
# JOBS_TO_PLAIN_TEXT  3  # Copy all incoming data to a txt file for each printjob
# JOBS_STRIP_ESCP2    4  # Create a txt file for each printjob but strip out ESC/P2 codes


def launch_escp2_converter(config):
    """Start escp2 converter

    If the config files contains a directory in `escp2_converter_path` setting,
    we expect that the binary is in this directory and has the name `convert-escp2`.

    convert-escp2 <path> <timeout> <retain_data> <printing> <endlesstext> <retain_pdf>

    Ex:
    convert-escp2 ./ 4 1 0 0 1

    Ex priority reg:
    nice -n19 <command>

    :param config: ConfigParser object
    :type config: configparser.ConfigParser
    :return: subprocess descriptor
    :rtype: subprocess.Popen
    """
    # Handle configuration filepaths
    converter_path = pathlib.Path(config["misc"]["escp2_converter_path"])

    if not converter_path.exists():
        LOGGER.error("Setting <escp2_converter_path:%s> doesn't exists!", converter_path)
        raise FileNotFoundError("escp2 converter not found")

    if converter_path.is_file():
        # Get directory
        working_dir = converter_path.parent
        binary = converter_path.name

    else:
        assert converter_path.is_dir()
        # Search default binary
        working_dir = converter_path
        binary = "convert-escp2"

        if not (working_dir / binary).is_file():
            LOGGER.error("convert-escp2 not found in <escp2_converter_path:%s> !", converter_path)
            raise FileNotFoundError("escp2 converter not found")

    # Launch as subprocess
    output_path = config["misc"]["output_path"]
    timeout     = 4  # Wait for more data in file; pause waiting new byte in file
    retain_data = 1  # Useless param didn't used
    printing    = 0  # Do not let the converter send pdf to printer => see jobs_to_printer_watchdog
    endlesstext = ENDLESS_TEXT_VALUE_MAPPING[config["misc"]["endlesstext"]]
    retain_pdf  = 1  # Useless param didn't used; endlesstext handle this behaviour

    cmd = "{}/{} {} {} {} {} {} {}".format(
        working_dir, binary, output_path, timeout, retain_data, printing, endlesstext, retain_pdf
    )
    args = shlex.split(cmd)
    LOGGER.debug("Subprocess command: %s", cmd)

    # Non blocking call => will be executed in background
    p = subprocess.Popen(args, cwd=working_dir)
    # 0 or -N if process is terminated (this should not be the case here)
    assert p.returncode is None

    LOGGER.debug("Subprocess PID: %s", p.pid)
    return p
