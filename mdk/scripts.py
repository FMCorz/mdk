#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2013 Frédéric Massart - FMCorz.net

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

import os
import shutil
import stat
import logging
from pkg_resources import resource_filename
from .tools import process
from .config import Conf
from .exceptions import ScriptNotFound, ConflictInScriptName, UnsupportedScript

C = Conf()


class Scripts(object):

    _supported = ['php', 'sh']
    _dirs = None
    _list = None

    @classmethod
    def dirs(cls):
        """Return the directories containing scripts, in priority order"""

        if not cls._dirs:
            dirs = ['~/.moodle-sdk']
            if C.get('dirs.moodle') != None:
                dirs.insert(0, C.get('dirs.moodle'))

            dirs.append('/etc/moodle-sdk')

            # Directory within the package.
            # This can point anywhere when the package is installed, or to the folder containing the module when it is not.
            packageDir = resource_filename('mdk', 'scripts')
            dirs.append(os.path.split(packageDir)[0])

            # Legacy: directory part of the root git repository, only if we can be sure that the parent directory is still MDK.
            if os.path.isfile(os.path.join(os.path.dirname(__file__), '..', 'mdk.py')):
                dirs.append(os.path.join(os.path.dirname(__file__), '..'))

            i = 0
            for d in dirs:
                dirs[i] = os.path.expanduser(os.path.join(d, 'scripts'))
                i += 1

            cls._dirs = dirs

        return cls._dirs

    @classmethod
    def list(cls):
        """Return a dict where keys are the name of the scripts
           and the value is the directory in which the script is stored"""

        if not cls._list:
            scripts = {}

            # Walk through the directories, in reverse to get the higher
            # priority last.
            dirs = cls.dirs()
            dirs.reverse()
            for d in dirs:

                if not os.path.isdir(d):
                    continue

                # For each file found in the directory.
                l = os.listdir(d)
                for f in l:

                    # Check if supported format.
                    supported = False
                    for ext in cls._supported:
                        if f.endswith('.' + ext):
                            supported = True
                            break

                    if supported:
                        scripts[f] = d

            cls._list = scripts

        return cls._list

    @classmethod
    def find(cls, script):
        """Return the path to a script"""

        lst = cls.list()
        cli = None
        if script in lst.keys():
            cli = os.path.join(lst[script], script)
        else:
            found = 0
            for ext in cls._supported:
                candidate = script + '.' + ext
                if candidate in lst.keys():
                    scriptFile = candidate
                    found += 1

            if found > 1:
                raise ConflictInScriptName('The script name conflicts with other ones')
            elif found == 1:
                cli = os.path.join(lst[scriptFile], scriptFile)

        if not cli:
            raise ScriptNotFound('Script not found')

        return cli

    @classmethod
    def run(cls, script, path, arguments=None, cmdkwargs={}):
        """Executes a script at in a certain directory"""

        # Converts arguments to a string.
        arguments = '' if arguments == None else arguments
        if type(arguments) == list:
            arguments = ' '.join(arguments)
        arguments = ' ' + arguments

        cli = cls.find(script)
        if cli.endswith('.php'):
            dest = os.path.join(path, 'mdkscriptrun.php')
            logging.debug('Copying %s to %s' % (cli, dest))
            shutil.copyfile(cli, dest)

            cmd = '%s %s %s' % (C.get('php'), dest, arguments)

            result = process(cmd, cwd=path, **cmdkwargs)
            os.remove(dest)
        elif cli.endswith('.sh'):
            dest = os.path.join(path, 'mdkscriptrun.sh')
            logging.debug('Copying %s to %s' % (cli, dest))
            shutil.copyfile(cli, dest)
            os.chmod(dest, stat.S_IRUSR | stat.S_IXUSR)

            cmd = '%s %s' % (dest, arguments)
            result = process(cmd, cwd=path, **cmdkwargs)
            os.remove(dest)
        else:
            raise UnsupportedScript('Script not supported')

        return result[0]
