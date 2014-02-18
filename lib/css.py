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
from tools import process
from config import Conf

C = Conf()


class Css(object):
    """Class wrapping CSS related functions"""

    _M = None

    def __init__(self, M):
        self._M = M

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

        for name in sheets:
            sheet = name + '.less'
            destSheet = name + '.css'

            if not os.path.isfile(os.path.join(source, sheet)):
                logging.warning('Could not find file %s' % (sheet))
                hadErrors = True
                continue

            try:
                compiler = Recess(source, os.path.join(source, sheet), os.path.join(dest, destSheet))
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

    def getThemePath(self, theme):
        return os.path.join(self._M.get('path'), 'theme', theme)


class Compiler(object):
    """LESS compiler abstract"""

    _compress = True
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


class CssCompileFailed(Exception):
    pass
