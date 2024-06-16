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
# Standard imports
from inspect import isfunction
import copy
import subprocess
import pytest
from watchdog.observers.inotify import InotifyObserver

# Custom imports
from libreprinter import plugins, plugins_handler
from libreprinter.file_handler import init_directories
# Import sample config fixture
from .test_config_parser import sample_config
# Import create dir fixture
from .test_file_handler import temp_dir



@pytest.fixture()
def handle_module_cache():
    """Regenerate the available set of plugins between tests

    Since the :meth:`libreprinter.plugins_handler._import_all` function
    deletes the plugins that don't match a given config, and that these plugins
    register themselves via the :meth:`libreprinter.plugins_handler.register`
    decorator, only 1 time at runtime, we must re-register them before a new
    test.
    """
    yield True

    # Tear down
    # Grab the plugins and import them
    plugin_modules = [
        plugins_handler._import("libreprinter.plugins", elem)
        for elem in dir(plugins)
        if elem.startswith("lp_")
    ]
    # Grab the functions to be registered (entry points of the plugins)
    funcs = [
        obj
        for elem in plugin_modules
        for obj_name, obj in elem.__dict__.items()
        if isfunction(obj)
        and obj_name.startswith("setup_")
        or obj_name.startswith("launch_")
    ]
    # Register these functions (refresh the _PLUGINS dict of the plugins_handler
    # module).
    _ = list(map(plugins_handler.register, funcs))


@pytest.mark.parametrize(
    "sample_config,expected",
    [
        # espc2_printer_enabled1: printer is not "no", txt file generated in txt_jobs/
        (
            """
            [misc]
            emulation=epson
            endlesstext=no
            output_printer=Fake_Printer_Name
            [parallel_printer]
            [serial_printer]
            """,
            # See lp_txt_converter config note for the explanation of its
            # presence here
            ["lp_escp2_converter", "lp_jobs_to_printer_watchdog", "lp_txt_converter"],
        ),
        # espc2_printer_enabled2: printer is not "no", txt file generated in txt_jobs/
        (
            """
            [misc]
            emulation=epson
            endlesstext=strip-escp2-jobs
            output_printer=Fake_Printer_Name
            [parallel_printer]
            [serial_printer]
            """,
            # See lp_txt_converter config note for the explanation of its
            # presence here
            ["lp_escp2_converter", "lp_jobs_to_printer_watchdog", "lp_txt_converter"],
        ),
        # escp2_printer_disabled: printer is "no", txt file generated in txt_jobs/
        (
            """
            [misc]
            emulation=epson
            endlesstext=no
            output_printer=no
            [parallel_printer]
            [serial_printer]
            """,
            # See lp_txt_converter config note for the explanation of its
            # presence here
            ["lp_escp2_converter", "lp_txt_converter"],
        ),
        # escp2_stream1: endlesstext is *stream: no txt in txt_jobs/, printer is disabled even if set
        (
            """
            [misc]
            emulation=epson
            endlesstext=strip-escp2-stream
            output_printer=Fake_Printer_Name
            [parallel_printer]
            [serial_printer]
            """,
            # See lp_txt_converter config note for the explanation of its
            # presence here
            ["lp_escp2_converter"],
        ),
        # escp2_stream2: endlesstext is *stream: no txt in txt_jobs/, printer is disabled even if set
        # plain-stream = no escp2 processing: no converter
        (
            """
            [misc]
            emulation=epson
            endlesstext=plain-stream
            output_printer=Fake_Printer_Name
            [parallel_printer]
            [serial_printer]
            """,
            [],
        ),
        # only_text: similar to epson emulation + plain-jobs as endlesstext
        # txt file generated in txt_jobs/
        (
            """
            [misc]
            emulation=text
            endlesstext=no
            output_printer=Fake_Printer_Name
            [parallel_printer]
            [serial_printer]
            """,
            ["lp_txt_converter", "lp_jobs_to_printer_watchdog"],
        ),
        # only_hp1: no txt in txt_jobs/
        (
            """
            [misc]
            emulation=hp
            endlesstext=no
            [parallel_printer]
            [serial_printer]
            """,
            ["lp_pcl_to_pdf_watchdog"],
        ),
        # only_hp2: no txt in txt_jobs/, printer is not "no" & enabled
        (
            """
            [misc]
            emulation=hp
            endlesstext=no
            output_printer=Fake_Printer_Name
            [parallel_printer]
            [serial_printer]
            """,
            ["lp_pcl_to_pdf_watchdog", "lp_jobs_to_printer_watchdog"],
        ),
        # hpgl: no endlesstext
        (
            """
            [misc]
            emulation=hpgl
            endlesstext=no
            [parallel_printer]
            [serial_printer]
            """,
            ["lp_hpgl_converter"],
        ),
        # postscript: no endlesstext
        (
            """
            [misc]
            emulation=postscript
            endlesstext=no
            [parallel_printer]
            [serial_printer]
            """,
            ["lp_ps_converter"],
        ),
    ],
    ids=[
        "espc2_printer_enabled1", "espc2_printer_enabled2", "escp2_printer_disabled",
        "escp2_stream1", "escp2_stream2",
        "only_text", "only_hp1", "only_hp2", "hpgl", "postscript",
    ],
    indirect=["sample_config"],  # Send sample_config val to the fixture
)
def test_plugins_loading(sample_config, expected, handle_module_cache, temp_dir):
    """Test the loading of plugins according to various configurations

    :param sample_config: (fixture) Parsed configuration
    :param expected: Expected list of enabled plugins for the given config
    :param handle_module_cache: (fixture) Regenerate the available set of
        plugins between tests.
    :param temp_dir: (fixture) Create temp directory
    :type sample_config: configparser.ConfigParser
    :type expected: list[str]
    :type handle_module_cache: bool
    :type temp_dir: str
    """
    init_directories(temp_dir)

    # Add temporary dir to config
    # Only mandatory if we want to start the plugin later
    sample_config["misc"]["output_path"] = temp_dir

    assert set(expected) == set(plugins.plugins(sample_config))

    if not expected:
        return

    # Get the entry point of the 1st plugin, execute it
    ret = plugins.call_functions(expected[0], sample_config)

    # Test the running subprocess type
    # => not mandatory here, functional tests are made in test_inteface & test_watchdogs
    assert isinstance(ret, (subprocess.Popen, InotifyObserver))

    # Tear down the process / watchdog
    if hasattr(ret, "stop"):
        # Watchdog
        ret.stop()
    else:
        # Process
        ret.kill()
