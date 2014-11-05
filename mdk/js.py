#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2014 Frédéric Massart - FMCorz.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

http://github.com/FMCorz/mdk
"""

import logging
import os
from .tools import process
from .config import Conf
from .plugins import PluginManager

C = Conf()


class Js(object):
    """Class wrapping JS related functions"""

    _M = None

    def __init__(self, M):
        self._M = M

    def shift(self, subsystemOrPlugin=None, module=None):
        """Runs shifter"""
        path = self.getYUISrcPath(subsystemOrPlugin, module=module)
        if not os.path.isdir(path):
            raise ValueError("The directory '%s' was not found" % (path))

        paths = []
        if module:
            paths.append(path)

        else:
            dirs = os.listdir(path)
            for d in dirs:
                if os.path.isdir(os.path.join(path, d, 'js')):
                    paths.append(os.path.join(path, d))

        shifter = Shifter(path)
        for path in paths:
            readablePath = path.replace(self._M.get('path'), '')
            logging.info('Shifting in %s' % readablePath)
            shifter.setCwd(path)
            shifter.compile()

    def document(self, outdir):
        """Runs documentator"""

        # TODO We should be able to generate outdir from here, using the workplace.
        path = self._M.get('path')
        documentor = Documentor(path, outdir)
        documentor.compile()

    def getYUISrcPath(self, subsystemOrPlugin, module=None):
        """Returns the path to the module, or the component"""

        try:
            path = PluginManager.getSubsystemDirectory(subsystemOrPlugin, M=self._M)
        except ValueError:
            (pluginType, name) = PluginManager.getTypeAndName(subsystemOrPlugin)
            path = PluginManager.getTypeDirectory(pluginType, M=self._M)
            # An exception will be thrown here if we do not find the plugin or component, that is fine.
            path = os.path.join(path, name)

        path = os.path.join(path, 'yui', 'src')
        if module:
            path = os.path.join(path, module)

        return path


class Shifter(object):

    _cwd = None

    def __init__(self, cwd=None):
        self.setCwd(cwd)

    def compile(self):
        """Runs the shifter command in cwd"""
        executable = C.get('shifter')
        if not executable or not os.path.isfile(executable):
            raise Exception('Could not find executable path %s' % (executable))

        cmd = [executable]
        (code, out, err) = process(cmd, cwd=self._cwd)
        if code != 0:
            raise ShifterCompileFailed('Error during shifting at %s' % (self._cwd))

    def setCwd(self, cwd):
        self._cwd = cwd


class Documentor(object):

    _cwd = None
    _outdir = None

    def __init__(self, cwd=None, outdir=None):
        self.setCwd(cwd)
        self.setOutdir(outdir)

    def compile(self):
        """Runs the yuidoc command in cwd"""
        executable = C.get('yuidoc')
        if not executable or not os.path.isfile(executable):
            raise Exception('Could not find executable path %s' % (executable))

        cmd = [executable, '--outdir', self._outdir]

        (code, out, err) = process(cmd, cwd=self._cwd)
        if code != 0:
            raise YuidocCompileFailed('Error whilst generating documentation')

    def setCwd(self, cwd):
        self._cwd = cwd

    def setOutdir(self, outdir):
        self._outdir = outdir


class YuidocCompileFailed(Exception):
    pass
class ShifterCompileFailed(Exception):
    pass
