"""Test config parser module with the text plugin loaded"""
# Standard imports
import pytest

# Custom imports
from libreprinter.commons import ESCAPY_BINARY
from libreprinter.plugins.lp_escapy_converter import configure_escapy as configure_func
from .test_config_parser import sample_config


@pytest.mark.parametrize(
    "sample_config,expected_settings",
    [
        # Config with user settings vs expected parsed settings
        (
            # default-settings
            """
            [misc]
            [parallel_printer]
            [serial_printer]
            """,
            {
                "escapy_path": ESCAPY_BINARY,
                "config_file": "/etc/escapy/escapy.conf",
            },
        ),
        (
            # empty-settings
            """
            [misc]
            [parallel_printer]
            [serial_printer]
            [escapy]
            escapy_path=
            config_file=
            """,
            {
                "escapy_path": ESCAPY_BINARY,
                "config_file": "/etc/escapy/escapy.conf",
            },
        ),
        (
            # edited-settings
            """
            [misc]
            [parallel_printer]
            [serial_printer]
            [escapy]
            escapy_path=XXX
            config_file=YYY
            """,
            {
                "escapy_path": "XXX",
                "config_file": "YYY",
            },
        ),
    ],
    ids=["default-settings", "empty-settings", "edited-settings"],
    indirect=["sample_config"],  # Send sample_config val to the fixture
)
def test_text_default_settings(sample_config, expected_settings):
    """Test default settings, user settings vs parsed ones

    The loading of the plugin is simulated since the configuration is checked
    on its side.
    """
    # Plugin loading simulation
    configure_func(sample_config)

    for k, v in expected_settings.items():
        assert sample_config["escapy"][k] == v, f"Fault key: {k}"
