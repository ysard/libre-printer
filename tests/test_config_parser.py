"""Test config parser module"""
# Standard imports
import os
import configparser
import pytest

# Custom imports
from libreprinter.config_parser import parse_config, load_config
from libreprinter.commons import ESCP2_CONVERTER, PCL_CONVERTER


def default_config():
    """Get default settings for different sections of the expected config file"""
    misc_section = {
        "start_cleanup": "no",
        "escp2_converter_path": ESCP2_CONVERTER,
        "pcl_converter_path": PCL_CONVERTER,
        "endlesstext": "no",
        "line_ending": "\n",
        "usb_passthrough": "no",
        "output_printer": "no",
        "serial_port": "/dev/ttyAMA0",
        "output_path": os.getcwd() + "/",
        "retain_data": "yes",
        "auto_end_page": "no",
        "end_page_timeout": "4",
        "emulation": "auto",
    }

    parallel_section = {
        "delayprinter": "0",
    }

    serial_section = {
        "dtr_logic": "high",
        "enabled": "no",
        "baudrate": "19200",
    }
    return misc_section, parallel_section, serial_section


# Data for test_default_settings()
TEST_DATA = [
    # Config with empty sections vs default expected config
    (
        """
        [misc]
        [parallel_printer]
        [serial_printer]
        """,
        default_config(),
    ),
    # Config with empty settings (interpreted as empty strings)
    # vs default expected config
    (
        """
        [misc]
        start_cleanup=
        escp2_converter_path=
        pcl_converter_path=
        endlesstext=
        line_ending=
        usb_passthrough=
        output_printer=
        serial_port=
        emulation=
        output_path=
        auto_end_page=
        end_page_timeout=
        retain_data=
        
        [parallel_printer]
        delayprinter=
        
        [serial_printer]
        dtr_logic=
        enabled=
        baudrate=
        """,
        default_config(),
    ),
]


@pytest.fixture()
def sample_config(request):
    """Fixture to parse config string and return initialised ConfigParser object

    :return: Parsed configuration
    :rtype: configparser.ConfigParser
    """
    config = configparser.ConfigParser()
    config.read_string(request.param)

    # Set default values
    # Default sections are expected from the given string
    return parse_config(config)


def test_empty_file():
    """Test empty config file"""
    sample_config = ""

    config = configparser.ConfigParser()
    config.read_string(sample_config)

    with pytest.raises(KeyError, match=r".*misc.*"):
        # Raises KeyError on not found section
        _ = parse_config(config)


@pytest.mark.parametrize(
    "sample_config,expected",
    TEST_DATA,
    ids=["empty_sections", "empty_settings"],
    indirect=["sample_config"],  # Send sample_config val to the fixture
)
def test_default_settings(sample_config, expected):
    """Test default settings set by the config parser in case of config file
    with empty sections or empty settings.
    """
    misc_section, parallel_section, serial_section = expected

    # Transtype for easier debugging (original object has a different string rep)
    found_misc_section = dict(sample_config["misc"])
    found_parallel_section = dict(sample_config["parallel_printer"])
    found_serial_section = dict(sample_config["serial_printer"])

    assert misc_section == found_misc_section
    assert parallel_section == found_parallel_section
    assert serial_section == found_serial_section

    # Test nb of settings (is there any not tested setting ?)
    expected = len(misc_section) + len(parallel_section) + len(serial_section)
    found = len(found_misc_section) + len(found_parallel_section) + len(found_serial_section)
    assert expected == found


@pytest.mark.parametrize(
    "sample_config,expected_settings",
    [
        # Config with user settings vs expected parsed settings
        (
            """
            [misc]
            line_ending=windows
            emulation=hp
            end_page_timeout=-1
            [parallel_printer]
            [serial_printer]
            """,
            {
                "line_ending": "\r\n",
                "emulation": "hp",
                "end_page_timeout": "4",  # <= 0 is not allowed
            },
        ),
        (
            """
            [misc]
            emulation=epson
            end_page_timeout=0
            [parallel_printer]
            [serial_printer]
            """,
            {
                "emulation": "epson",
                "end_page_timeout": "4",  # <= 0 is not allowed
            },
        ),
    ],
    ids=["sample1", "sample2"],
    indirect=["sample_config"],  # Send sample_config val to the fixture
)
def test_specific_settings(sample_config, expected_settings):
    """Test user settings vs parsed ones"""
    for k, v in expected_settings.items():
        assert sample_config["misc"][k] == v
