#  Libreprinter is a software allowing to use the Centronics and serial printing
#  functions of vintage computers on modern equipement through a tiny hardware
#  interface.
#  Copyright (C) 2020-2024  Ysard
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Test launch of the escp2 converter inside a subprocess

.. seealso:: :meth:`test_interface.test_endlesstext_values` for functional tests
    of the escp2 converter.
"""
# Standard imports
import pytest

# Custom imports
from libreprinter.plugins.lp_escp2_converter import launch_escp2_converter
from libreprinter.commons import ESCP2_CONVERTER

# Import create dir fixture
from .test_file_handler import temp_dir


@pytest.fixture()
def sample_config(temp_dir):
    """Simulate the smallest required settings for escp2 converter binary

    Only escp2_converter_path, output_path, endlesstext in misc section
    are expected.
    """
    config = {
        "misc": {
            "escp2_converter_path": ESCP2_CONVERTER,
            "output_path": temp_dir,
            "endlesstext": "no",
        }
    }
    return config


def test_escp2_converter(sample_config):
    """Test normal execution of subprocess for escp2 converter"""
    process = launch_escp2_converter(sample_config)
    assert process

    # Clean up
    process.kill()


@pytest.mark.parametrize(
    "fake_binary_path",
    [
        "im_fake.bin",  # Fake binary
        "/tmp",  # Directory without binary inside
    ],
)
def test_escp2_converter_no_binary(sample_config, fake_binary_path):
    """Test with absent escp2 converter expected binary
    (no binary & no binary inside dir)
    """
    # Simulate fake binary
    sample_config["misc"]["escp2_converter_path"] = fake_binary_path

    with pytest.raises(FileNotFoundError, match=r"escp2 converter not found"):
        _ = launch_escp2_converter(sample_config)
