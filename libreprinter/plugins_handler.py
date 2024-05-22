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
"""Handle the dynamic loading of plugins"""
# Standard imports
import functools
import importlib
from collections import namedtuple

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources
# Custom imports
from libreprinter import commons as cm

LOGGER = cm.logger()

# Basic structure for storing information about one plugin
Plugin = namedtuple("Plugin", ("name", "func"))

# Dictionary with information about all registered plugins
_PLUGINS = {}


def register(func):
    """Decorator for registering a new plugin"""
    package, _, plugin = func.__module__.rpartition(".")
    pkg_info = _PLUGINS.setdefault(package, {})
    pkg_info[plugin] = Plugin(name=plugin, func=func)
    return func


def names(package, config):
    """Import modules in the given package & return all plugins in it

    :param package: Name of the Python package in which plugins can be found
    :param config: ConfigParser object
    :type package: str
    :type config: configparser.ConfigParser
    :return: List of modules sorted in lexical order
    :rtype: List[str]
    """
    _import_all(package, config)
    if not _PLUGINS:
        return []
    return sorted(_PLUGINS[package])


def get(package, plugin):
    """Get the entry point function of the given plugin"""
    _import(package, plugin)
    return _PLUGINS[package][plugin].func


def call(package, plugin, *args, **kwargs):
    """Execute the entry point function of the given plugin"""
    plugin_func = get(package, plugin)
    return plugin_func(*args, **kwargs)


def _import(package, plugin):
    """Import the given plugin file from a package

    :return: The imported module object
    :rtype: module
    """
    return importlib.import_module(f"{package}.{plugin}")


def _import_all(package, config):
    """Import all plugins (modules) in a package

    Modules are also filtered according to the given configuration.
    If a param is not compatible with the current configuration, the plugin
    will not be enabled.

    Plugin names must be Python files starting with "lp_".
    Their configuration must be in a global variable `CONFIG`.

    :param package: Name of the Python package in which plugins can be found
    :param config: ConfigParser object
    :type package: str
    :type config: configparser.ConfigParser
    """
    # Find installed plugins
    plugin_names = [
        module[:-3]
        for module in resources.contents(package)
        if module.endswith(".py") and module.startswith("lp_")
    ]
    # Filter plugins according to their compatibility with the current config
    for plugin in plugin_names:
        module = _import(package, plugin)

        if not is_plugin_compatible(config, module.CONFIG):
            LOGGER.debug("Delete plugin: %s", plugin)
            del _PLUGINS[package][plugin]

    LOGGER.info(
        "Plugins loaded: %s",
        [name for plugins in _PLUGINS.values() for name in plugins.keys()]
    )


def is_plugin_compatible(current_config, plugin_config):
    """Get the compatibility of a config from a plugin vs current user config

    :param current_config: ConfigParser object
    :param plugin_config: Dictionnary of sections and params
    :return: True if the plugin is compatible, False otherwise.
        .. note:: An empty plugin configuration will return True (permanent plugin)
    :type current_config: configparser.ConfigParser
    :type plugin_config: dict
    """
    for p_section_name, p_section in plugin_config.items():
        c_section = dict(current_config).get(p_section_name)
        if not c_section:
            # Plugin section not in expected current config (:o)
            return False

        for p_param_name, p_param in p_section.items():
            # Handle multiple possible params compatible with this plugin
            # Params can be an iterable or a fixed string
            # print("mod param:", p_param_name, ":", p_param, "vs", c_section.get(p_param_name))
            if (
                isinstance(p_param, (list, tuple))
                and c_section.get(p_param_name) not in p_param
            ) or (isinstance(p_param, str) and c_section.get(p_param_name) != p_param):
                return False
            elif callable(p_param):
                # Execute the callable to get a test result
                return p_param(c_section.get(p_param_name))
    return True


def names_factory(package):
    """Create a names() function for one package

    Usage:
        In plugins/__init__.py:
            `plugins = plugins_handler.names_factory(__package__)`
        After import:
            `plugins(args_for_names_function)`
    """
    return functools.partial(names, package)


def get_factory(package):
    """Create a get() function for one package

    Usage:
        In plugins/__init__.py:
            `get_functions = plugins_handler.get_factory(__package__)`
        After import:
            `get_functions(plugin_name)(args_for_plugin_function)`
    """
    return functools.partial(get, package)


def call_factory(package):
    """Create a call() function for one package

    Usage:
        In plugins/__init__.py:
            `call_functions = plugins_handler.call_factory(__package__)`
        After import:
            `call_functions(plugin_name, args_for_plugin_function)`
    """
    return functools.partial(call, package)
