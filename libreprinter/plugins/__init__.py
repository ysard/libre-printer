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
"""Package with routines to access the plugins (Python modules) stored in the
current subdirectory.

Usage::

    plugins(args_for_names_function)
    get_functions(plugin_name)(args_for_plugin_function)
    call_functions(plugin_name, args_for_plugin_function)
"""

from libreprinter import plugins_handler

plugins = plugins_handler.names_factory(__package__)
call_functions = plugins_handler.call_factory(__package__)
get_functions = plugins_handler.get_factory(__package__)
