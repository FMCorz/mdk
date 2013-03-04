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

import argparse
import sys
import workplace


class Command(object):
    """Represents a command"""

    _arguments = [
            (
                ['foo'],
                {
                    'help': 'I\'m an argument'
                }
            ),
            (
                ['-b', '--bar'],
                {
                    'action': 'store_true',
                    'help': 'I\'m a flag'
                }
            )
        ]
    _description = 'Undocumented command'

    __C = None
    __Wp = None

    def __init__(self, config):
        self.__C = config
        self.__Wp = workplace.Workplace()

    @property
    def arguments(self):
        return self._arguments

    @property
    def C(self):
        return self.__C

    @property
    def description(self):
        return self._description

    def resolve(self, name):
        return self.Wp.resolve(name)

    def resolveMultiple(self, names):
        return self.Wp.resolve(names)

    def run(self, args):
        return True

    @property
    def Wp(self):
        return self.__Wp


class CommandRunner(object):
    """Executes a command"""

    def __init__(self, command):
        self._command = command

    @property
    def command(self):
        return self._command

    def run(self, sysargs=sys.argv, prog=None):
        parser = argparse.ArgumentParser(description=self.command.description, prog=prog)
        for argument in self.command.arguments:
            args = argument[0]
            kwargs = argument[1]
            if 'sub-commands' in kwargs:
                subs = kwargs['sub-commands']
                del kwargs['sub-commands']
                subparsers = parser.add_subparsers(**kwargs)
                for name, sub in subs.items():
                    subparser = subparsers.add_parser(name, **sub[0])
                    defaults = {args[0]: name}
                    subparser.set_defaults(**defaults)
                    for subargument in sub[1]:
                        sargs = subargument[0]
                        skwargs = subargument[1]
                        subparser.add_argument(*sargs, **skwargs)
            else:
                parser.add_argument(*args, **kwargs)
        args = parser.parse_args(sysargs)
        self.command.run(args)


if __name__ == "__main__":
    RunCommand(Command()).run()
