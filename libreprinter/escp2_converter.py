# Standard imports
import shlex
import subprocess
import pathlib
# Custom imports
import libreprinter.commons as cm

LOGGER = cm.logger()


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
    timeout = 4
    retain_data = 1
    printing = 0
    endlesstext = int(config["misc"]["endlesstext"] != "no")  # 0 if "no"
    retain_pdf = 1

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
