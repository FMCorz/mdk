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

C = Conf()


class Css(object):
    """Class wrapping CSS related functions"""

    _M = None

    _debug = False
    _compiler = 'grunt'

    def __init__(self, M):
        self._M = M

    def setCompiler(self, compiler):
        self._compiler = compiler

    def setDebug(self, debug):
        self._debug = debug

    def compile(self, theme='bootstrapbase', sheets=None):
        """Compile LESS sheets contained within a theme"""

        source = self.getThemeLessPath(theme)
        dest = self.getThemeCssPath(theme)
        if not os.path.isdir(source):
            raise Exception('Unknown theme %s, or less directory not found' % (theme))

        if not sheets:
            # Guess the sheets from the theme less folder.
            sheets = []
            for candidate in os.listdir(source):
                if os.path.isfile(os.path.join(source, candidate)) and candidate.endswith('.less'):
                    sheets.append(os.path.splitext(candidate)[0])
        elif type(sheets) != list:
            sheets = [sheets]

        if len(sheets) < 1:
            logging.warning('Could not find any sheets')
            return False

        hadErrors = False

        if self._compiler == 'grunt':
            sheets = ['moodle']

        for name in sheets:
            sheet = name + '.less'
            destSheet = name + '.css'

            if not os.path.isfile(os.path.join(source, sheet)):
                logging.warning('Could not find file %s' % (sheet))
                hadErrors = True
                continue

            try:
                if self._compiler == 'grunt':
                    compiler = Grunt(source, os.path.join(source, sheet), os.path.join(dest, destSheet))
                elif self._compiler == 'recess':
                    compiler = Recess(source, os.path.join(source, sheet), os.path.join(dest, destSheet))
                elif self._compiler == 'lessc':
                    compiler = Lessc(self.getThemeDir(), os.path.join(source, sheet), os.path.join(dest, destSheet))

                compiler.setDebug(self._debug)

                compiler.execute()
            except CssCompileFailed:
                logging.warning('Failed compilation of %s' % (sheet))
                hadErrors = True
                continue
            else:
                logging.info('Compiled %s to %s' % (sheet, destSheet))

        return not hadErrors

    def getThemeCssPath(self, theme):
        return os.path.join(self.getThemePath(theme), 'style')

    def getThemeLessPath(self, theme):
        return os.path.join(self.getThemePath(theme), 'less')

    def getThemeDir(self):
        return os.path.join(self._M.get('path'), 'theme')

    def getThemePath(self, theme):
        return os.path.join(self.getThemeDir(), theme)


class Compiler(object):
    """LESS compiler abstract"""

    _compress = True
    _debug = False
    _cwd = None
    _source = None
    _dest = None

    def __init__(self, cwd, source, dest):
        self._cwd = cwd
        self._source = source
        self._dest = dest

    def execute(self):
        raise Exception('Compiler does not implement execute() method')

    def setCompress(self, compress):
        self._compress = compress

    def setDebug(self, debug):
        self._debug = debug


class Grunt(Compiler):
    """Grunt compiler"""

    def execute(self):
        executable = C.get('grunt')
        if not executable:
            raise Exception('Could not find executable path')

        cmd = [executable, 'css']

        (code, out, err) = process(cmd, self._cwd)
        if code != 0 or len(out) == 0:
            raise CssCompileFailed('Error during compile')


class Recess(Compiler):
    """Recess compiler"""

    def execute(self):
        executable = C.get('recess')
        if not executable:
            raise Exception('Could not find executable path')

        cmd = [executable, self._source, '--compile']

        if self._compress:
            cmd.append('--compress')

        (code, out, err) = process(cmd, self._cwd)
        if code != 0 or len(out) == 0:
            raise CssCompileFailed('Error during compile')

        # Saving to destination
        with open(self._dest, 'w') as f:
            f.write(out)


class Lessc(Compiler):
    """Lessc compiler"""

    def execute(self):
        executable = C.get('lessc')
        if not executable:
            raise Exception('Could not find executable path')

        cmd = [executable]

        sourcePath = os.path.relpath(self._source, self._cwd)
        sourceDir = os.path.dirname(sourcePath)

        if self._debug:
            cmd.append('--source-map-rootpath=' + sourceDir)
            cmd.append('--source-map-map-inline')
            self.setCompress(False)

        if self._compress:
            cmd.append('--compress')

        # Append the source and destination.
        cmd.append(sourcePath)
        cmd.append(os.path.relpath(self._dest, self._cwd))

        (code, out, err) = process(cmd, self._cwd)
        if code != 0 or len(out) != 0:
            raise CssCompileFailed('Error during compile')


class CssCompileFailed(Exception):
    pass
