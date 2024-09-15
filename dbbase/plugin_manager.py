"""
plugin_manager.py - plugin interface

# **********************************************************************
#       This is plugin_manager.py, part of DBBase.
#       Copyright (c) 2024 David Lowry-Duda <david@lowryduda.com>
#       All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
#                 <http://www.gnu.org/licenses/>.
# **********************************************************************
"""
class PluginManager:
    def __init__(self):
        self.plugins = []

    def load_plugin(self, plugin):
        """
        Register a plugin.
        """
        self.plugins.append(plugin)

    def call_hook(self, hook_name, *args, **kwargs):
        """
        Call the given hook on all plugins, passing in any arguments.
        """
        for plugin in self.plugins:
            hook = getattr(plugin, hook_name, None)
            if callable(hook):
                hook(*args, **kwargs)


plugin_manager = PluginManager()
