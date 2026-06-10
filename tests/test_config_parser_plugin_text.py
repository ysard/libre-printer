"""Test config parser module with the text plugin loaded"""
# Standard imports
import pytest

# Custom imports
from libreprinter.commons import ENSCRIPT_BINARY
from libreprinter.plugins.lp_txt_converter import configure_text as configure_func
from .test_config_parser import sample_config


@pytest.mark.parametrize(
    "sample_config,expected_settings",
    [
        # Config with user settings vs expected parsed settings
        (
            # default-settings
            """
            [misc]
            emulation=text
            [parallel_printer]
            [serial_printer]
            """,
            {
                "enscript_path": ENSCRIPT_BINARY,
                "enscript_settings": "-BR",
            },
        ),
        (
            # empty-settings
            """
            [misc]
            emulation=text
            [text]
            enscript_path=
            enscript_settings=
            [parallel_printer]
            [serial_printer]
            """,
            {
                "enscript_path": ENSCRIPT_BINARY,
                "enscript_settings": "-BR",
            },
        ),
        (
            # edited-settings
            """
            [misc]
            emulation=text
            [parallel_printer]
            [serial_printer]
            [text]
            enscript_path=XXX
            enscript_settings=YYY
            """,
            {
                "enscript_path": "XXX",
                "enscript_settings": "YYY",
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
        assert sample_config["text"][k] == v, f"Fault key: {k}"
