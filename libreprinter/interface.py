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
"""Group of functions that communicate with the interface via the serial port

- initialisation
- configuration
- data receiving
"""
# Standard imports
import shutil
import logging
from packaging.version import Version

# Custom imports
from libreprinter.file_handler import (
    get_job_number,
    convert_file_line_ending,
    convert_data_line_ending,
)
from libreprinter.legacy_interprocess_com import (
    initialize_interprocess_com,
    send_status_message,
    debug_shared_memory,
)
from libreprinter.handlers import get_serial_handler, SerialException
from libreprinter.commons import logger, LAST_HARDWARE_VERSION
from libreprinter.config_parser import FLOW_CTRL_MAPPING

LOGGER = logger()


def build_interface_config_settings(config):
    r"""Build configuration strings ready to be sent to the interface

    About `enabled` param of `serial_printer` config section:

        - no: Only parallel printer will be working
            => send only parallel config
        - yes: Only serial printer will be working
            => send only serial config

    :param config: ConfigParser object
    :type config: configparser.ConfigParser
    :return: List of settings (form: `<param>=<value>\n`).
    :rtype: list[str]
    """
    interface_params = []

    serial_section = config["serial_printer"]
    serial_enabled = serial_section.get("enabled")
    if serial_enabled != "no":
        # Serial printer only or automatic
        # DTR config:
        #   1: printer is ready when DSR is asserted (space high level) (default)
        #   0: printer is ready when DSR is deasserted (mark low level) (CP2102)
        dtr_logic = serial_section.get("dtr_logic") != "low"
        interface_params.append("dtr_logic={}\n".format(int(dtr_logic)))

        if serial_enabled == "yes":
            # PS: auto: do not sent param, let the interface choose
            interface_params.append("serial_enabled=1\n")
        elif serial_enabled == "auto":
            raise NotImplementedError

        baudrate = serial_section.getint("baudrate")
        interface_params.append(f"baudrate={baudrate}\n")

        flow_control = serial_section.get("flow_control")
        interface_params.append(f"flow_control={FLOW_CTRL_MAPPING[flow_control]}\n")

    if serial_enabled != "yes":
        # Parallel printer only or serial automatic
        parallel_section = config["parallel_printer"]
        delayprinter = parallel_section.get("delayprinter")
        interface_params.append(f"delayprinter={delayprinter}\n")

    return interface_params


def configure_interface(serial_handler, config):
    """Send settings of the session to the interface via the serial port

    Configuration process description:

        .. mermaid::

            sequenceDiagram
            Host->>+Printer: param=value
            Printer->>Host: param: value
            Host->>Printer: ...
            Printer->>Host: ...
            Host->>Printer: end_config
            Printer->>Host: Serial/Parallel printer configured!
            Printer->>-Host: end_config

    :param serial_handler: Serial port handler.
    :param config: ConfigParser object
    :type serial_handler: serial.Serial
    :type config: configparser.ConfigParser
    """
    LOGGER.debug("Send config to the interface...")

    [serial_handler.write(param.encode()) for param in build_interface_config_settings(config)]
    # Signal end of config
    serial_handler.write(b"end_config\n")

    LOGGER.info("Config sent to the interface.")

    # Wait config ack
    while True:
        response = serial_handler.readline().decode("utf8")

        if response:
            LOGGER.debug(response.rstrip())
        else:
            LOGGER.debug("Waiting config aknowledgment...")
            continue

        if response.startswith("Online version"):
            remote_version = Version(response.split()[2])
            if remote_version < Version(LAST_HARDWARE_VERSION):
                LOGGER.warning(
                    "The remote firmware is not up to date! (%s vs %s)",
                    remote_version,
                    LAST_HARDWARE_VERSION
                )

        if response.startswith("end_config"):
            break


def apply_msb_control(databyte, msbsetting):
    """Apply MSB control command to the given byte

    .. note:: This kind of control codes is deprecated according to the Epson
        datasheet. Not many printers should use them...

    :param databyte: Supposed modified byte
    :param msbsetting: Expects value in (0: No modification,
        1: MSB (bit 7) is set to 0, 2: MSB (bit 7) is set to 1).
    :type databyte: bytes
    :type msbsetting: int
    :return: Modified value; value derived from unsigned int (c_uint8)
    :rtype: int
    """
    if msbsetting == 0:
        # Cancel MSB Control: No control on bit 7
        return databyte
    elif msbsetting == 1:
        # MSB Control: clear bit 7 (to 0)
        return databyte[0] & 0x7f  # Get only 8 bits: convert to unsigned int
    elif msbsetting == 2:
        # MSB Control: set bit 7 (to 1)
        return databyte[0] | 0x80  # Get only 8 bits: convert to unsigned int

    raise ValueError("msbsetting value not expected: %s" % msbsetting)


def is_bit_set(byte, bit_number):
    """Test if nth bit is set in the given byte

    :param byte: databyte to test
    :param bit_number: nth bit number to test in databyte
    :type byte: bytes
    :type bit_number: int
    :return: Result of test
    :rtype: boolean
    """
    # get a simple yes/no 1/0 answer
    # right shift and get the least-significant bit
    return bool((byte[0] >> bit_number) & 1)


def get_buffer(serial_handler, end_page_timeout):
    """Try to read and return bytes from interface

    Serial read timeout = end_page_timeout defined in config.

    :param serial_handler: Serial port handler.
    :param end_page_timeout: Timeout in seconds used to define the number of
        retries in case of empty buffer.
        Serial read is in blocking mode (1sec per try).
    :type serial_handler: serial.Serial
    :type end_page_timeout: int
    :return: None in case of no response or timeout, a bytearray otherwise.
    """
    error_count = 0

    while error_count < end_page_timeout:
        # Arbitrary length
        response = bytearray(serial_handler.read(size=8000))
        if response:
            # Signal the conversion program that capture program is controlling leds
            # send_status_message(200, 2)
            return response

        error_count += 1
    # Signal the conversion program that it can control leds
    # send_status_message(200, 1)


def parse_buffer(serial_handler, job_number, config):
    """
    TODO: penser à coroutine:
        générateur emettant des databytes
        + un flag de fin de page (tant que pas envoyé, écriture dans le même fichier)
        + flag emulation

    STREAM_PLAIN_TEXT || STREAM_STRIP_ESCP2
        just put data in the same file during receiving
        and sync converter for STREAM_STRIP_ESCP2

    NO_PLAIN_TEXT || JOBS_TO_PLAIN_TEXT => parent loop
    JOBS_STRIP_ESCP2: handled by converter

    - usbpassthrough:
        - enabled: store a raw file and then put it in the given peripheral
        - disabled: store a raw file and alert converters of the job status

    :param serial_handler: Serial port handler.
    :param job_number:
    :param config:
    :type serial_handler: serial.Serial
    """
    # Handle USB passthrough
    usb_printer_dev_f_d = None
    if config["misc"]["usb_passthrough"] != "no":
        # Epson + HP
        # => write directly in /dev/ interface
        usb_printer_dev_f_d = open(
            config["misc"]["usb_passthrough"], "wb"
        )

    epson_emulation = config["misc"]["emulation"] == "epson"

    # Handle data stream and stream plain text
    stream = plain_stream_f_d = line_ending = None
    if epson_emulation and "stream" in config["misc"]["endlesstext"]:
        # Epson: plain-stream/strip-escp2-stream
        # Put the data in the same file (infinite loop)
        # PS: do not forget to sync converter if no plain (see below)
        stream = True
        if "plain" in config["misc"]["endlesstext"]:
            # Process line endings and put the result in txt_stream/ dir
            line_ending = config["misc"]["line_ending"].encode()

            plain_stream_f_d = open(
                "{}txt_stream/{}.txt".format(config["misc"]["output_path"], job_number),
                "wb",
            )

    raw_f_d = open(
        "{}raw/{}.raw".format(config["misc"]["output_path"], job_number), "wb"
    )

    # Epson control
    escimode = False
    escmode = False
    print_controlcodes = False
    italic = False
    masterfontmode = False
    msbsetting = 0

    # Misc
    received_bytes = False
    end_page_timeout = config["misc"].getint("end_page_timeout")

    # Read interface and process bytes if necessary
    while True:
        databytes = get_buffer(serial_handler, end_page_timeout)
        if not databytes:
            # No data during configured timeout
            if received_bytes and not stream:
                LOGGER.info("End of page timeout")
                # Job is terminated: close file descriptors
                raw_f_d.close()

                if usb_printer_dev_f_d:
                    usb_printer_dev_f_d.close()
                # Exit loop
                return

            if stream:
                raw_f_d.flush()
            if plain_stream_f_d:
                plain_stream_f_d.flush()

            received_bytes = False
            LOGGER.debug("Waiting data...")
            continue

        # print("in:", databytes)
        # LOGGER.debug("in: %s", databytes)

        # TODO: autodetect epson_emulation based on init seq
        # TODO: starts_with ?
        if not received_bytes and b"\x1B\x40\x1B" in databytes:
            # Epson init command /end printing command (\x1B@\x1B)
            print("PROBE EPSON data")
        if not received_bytes and b"\x1B\x45\x1B\x26\x6c" in databytes:
            # HP reset/init command (\x1BE\x1B&l) (0x1B E)
            print("PROBE HP data")

        received_bytes = True

        if epson_emulation:

            for index, databyte in enumerate(databytes):
                if msbsetting != 0:
                    databyte = apply_msb_control(databyte, msbsetting)
                    databytes[index] = databyte

                # All this stuff is designed to set status of print_controlcodes
                # and so set msbsetting which ultimately modifies the current
                # databyte...
                # These checks ARE NOT made by espc2 converter for some reason...
                # Check ESC command
                if (databyte == 27) and not print_controlcodes:
                    escmode = True
                elif escmode:

                    if databyte == ord("#"):
                        # Cancel MSB Control; escp2 line 3437
                        msbsetting = 0
                    if databyte == ord("="):
                        # Set MSB (bit 7) of all incoming data to 0
                        msbsetting = 1
                    if databyte == ord(">"):
                        # Set MSB (bit 7) of all incoming data to 1
                        msbsetting = 2
                    if databyte == ord("I"):
                        # ESC I n - enable printing of control codes - shaded codes in table in manual (A-23); escp2 line 3528
                        escimode = True
                    if databyte == ord("4"):
                        # ESC 4 SELECT ITALIC FONT; escp2 line 2860
                        italic = True
                    if databyte == ord("5"):
                        # ESC 5 CANCEL ITALIC FONT
                        italic = False
                    if databyte == ord("!"):
                        # ESC ! n Master Font Select
                        masterfontmode = True
                    escmode = False
                elif escimode:
                    if not italic:
                        print_controlcodes = databyte == 1
                    escimode = False

                elif masterfontmode:
                    # Test if 6th bit is set
                    # yes: select italic
                    # no: cancel italic
                    italic = is_bit_set(databyte, 6)
                    masterfontmode = False

            if plain_stream_f_d:
                # plain-stream
                plain_stream_f_d.write(convert_data_line_ending(databytes, line_ending))

        # Save received data
        # print("out:", databytes)
        raw_f_d.write(databytes)

        if epson_emulation and stream and not plain_stream_f_d:
            # Not plain-stream, but strip-escp2-stream
            # => need to sync escp2 converter
            raw_f_d.flush()
            # Experimental sync
            sync_converters(0, job_number)

        if usb_printer_dev_f_d:
            # usb_passthrough enabled: forward bytes
            usb_printer_dev_f_d.write(databytes)


def read_interface(config):
    """Entry point and infinite loop to read serial interface

    :param config: ConfigParser object
    :type config: configparser.ConfigParser
    """
    misc_section = config["misc"]

    # Get serial connection
    serial_handler = get_serial_handler(misc_section["serial_port"])
    # LOGGER.debug(serial_handler)
    if not serial_handler:
        return

    # Setup interface
    configure_interface(serial_handler, config)

    # Setup communication with espc2 converter
    shared_mem_f_d = initialize_interprocess_com()

    # Signal the conversion program that it can control leds
    # send_status_message(200, 1)

    job_number = get_job_number(misc_section["output_path"])
    # TODO: Set job_number according to pending jobs in shared memory and
    #   real pending files in /raw dir
    LOGGER.debug("Current job number: %s", job_number)

    # Number of jobs for the current session (equiv "cnt" variable in legacy prog)
    # jobs_count: slot in shared memory
    # job_number: job number used in page naming by converters
    # TODO: set job_count according to free slots in shared memory
    jobs_count = 0
    while True:
        # TODO: epson: jobs | no plain text: verif slot: get_status_message(cnt) == 0 => boucle while d'attente ?

        # TODO: redéfinier emulation à l'origine ?
        # ou passer toutes les fonctions qyi suivent à la fin de parse_buffer...
        try:
            parse_buffer(serial_handler, job_number, config)
        except SerialException as e:
            # Properly ends the infinite loop after an error on the serial pipe
            LOGGER.exception(e)
            break

        epson_emulation = misc_section["emulation"] == "epson"

        LOGGER.debug(
            "epson ? %s, usb_passthrough ? %s",
            epson_emulation, misc_section["usb_passthrough"]
        )

        if epson_emulation and misc_section["usb_passthrough"] == "no":
            # No conversion if usb_passthrough is enabled
            # Since raw and pcl converters are implemented here,
            # sync of converter should be made only for epson (espc2):
            # no plain text | strip-escp2-jobs.
            # strip-escp2-stream is made during the loop.
            sync_converters(jobs_count, job_number)

        if misc_section["emulation"] == "hp":
            # Copy current file to pcl folder
            shutil.copy(
                "{}/raw/{}.raw".format(misc_section["output_path"], job_number),
                "{}/pcl/{}.pcl".format(misc_section["output_path"], job_number),
            )

        if (
            config["misc"]["emulation"] == "text"
            or (epson_emulation and (misc_section["endlesstext"] == "plain-jobs"))
        ):
            # Process end of lines in raw file and copy it to /txt_jobs dir
            convert_file_line_ending(
                "{}/raw/{}.raw".format(misc_section["output_path"], job_number),
                "{}/txt_jobs/{}.txt".format(misc_section["output_path"], job_number),
                config["misc"]["line_ending"],
            )

        if jobs_count >= 199:
            # Arbitrary limit
            jobs_count = 0

        jobs_count += 1
        job_number += 1

    # Should never be reached unless the link to the interface has been broken
    serial_handler.close()
    # Close opened shared mem in initialize_interprocess_com()
    shared_mem_f_d.close()


def sync_converters(jobs_count, job_number):
    """Synchronize status of the current job with converters
    Basically we send job and page numbers in order that the converter processes
    the pending file.
    """
    LOGGER.debug("Sync job %s, number %s", jobs_count, job_number)
    # Negative page: end of page
    send_status_message(jobs_count, -job_number)

    # Signal raw convertors that we have captured some more data
    # Only useful for STREAM_STRIP_ESCP2 or STREAM_PLAIN_TEXT
    send_status_message(202, 1)

    # Signal the conversion program that it can control leds
    # Mandatory to solve a bug (blocking useless test) in convertors that
    # prevent them to process the page if this signal is not sent ><
    send_status_message(200, 1)

    # Wait until the conversion programs have finished reading the file to
    # limit concurrent accesses.
    # STREAM_STRIP_ESCP2 or STREAM_PLAIN_TEXT
    # Spoiler: not ok on 3.7+, poke 202 is not reset to 0 by convertors...
    # => Wait of 0 value in jobs_count packet => not implemented

    # Show memory status
    if LOGGER.getEffectiveLevel() == logging.DEBUG:
        debug_shared_memory()
