"""Test config parser module with the text plugin loaded"""
# Standard imports
import pytest

# Custom imports
from libreprinter.plugins.lp_seiko_qt2100_converter import configure_seiko as configure_func
from .test_config_parser import sample_config


@pytest.mark.parametrize(
    "sample_config,expected_settings",
    [
        # Config with user settings vs expected parsed settings
        (
            # default-settings
            """
            [misc]
            emulation=seiko-qt2100
            [parallel_printer]
            [serial_printer]
            """,
            {
                "enable-csv": "yes",
                "enable-graph": "yes",
                "vertical": "yes",
                "cutoff": "true",
            },
        ),
        (
            # edited-settings
            """
            [misc]
            emulation=seiko-qt2100
            [parallel_printer]
            [serial_printer]
            [seiko-qt2100]
            enable-graph=xxx
            cutoff=false
            vertical=no
            """,
            {
                "enable-csv": "yes",
                "enable-graph": "no",  # garbage fixed
                "vertical": "no",
                "cutoff": "false",
            },
        ),
        (
            # numeric-cutoff
            """
            [misc]
            emulation=seiko-qt2100
            [parallel_printer]
            [serial_printer]
            [seiko-qt2100]
            cutoff=1.0
            """,
            {
                "cutoff": "1.0",  # tristate variable parsed (bool, float, int)
            },
        ),
    ],
    ids=["default-settings", "edited-settings", "numeric-cutoff"],
    indirect=["sample_config"],  # Send sample_config val to the fixture
)
def test_seiko_default_settings(sample_config, expected_settings):
    """Test default settings, user settings vs parsed ones

    The loading of the plugin is simulated since the configuration is checked
    on its side.
    """
    # Plugin loading simulation
    configure_func(sample_config)

    for k, v in expected_settings.items():
        assert sample_config["seiko-qt2100"][k] == v, f"Fault key: {k}"
