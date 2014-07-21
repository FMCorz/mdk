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

    def argumentError(self, message):
        raise CommandArgumentError(message)

    @property
    def arguments(self):
        return self._arguments

    @property
    def C(self):
        return self.__C

    @property
    def description(self):
        return self._description

    def run(self, args):
        return True

    @property
    def Wp(self):
        if not self.__Wp:
            from .workplace import Workplace
            self.__Wp = Workplace()
        return self.__Wp


class CommandArgumentError(Exception):
    """Exception when a command sends an argument error"""
    pass


class CommandArgumentFormatter(argparse.HelpFormatter):
    """Custom argument formatter"""

    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            forbiddentypes = ['_StoreTrueAction', '_StoreFalseAction']
            if action.__class__.__name__ not in forbiddentypes and action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += ' (default: %(default)s)'
        return help


class CommandArgumentParser(argparse.ArgumentParser):
    """Custom argument parser"""

    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, '\n%s: error: %s\n' % (self.prog, message))


class CommandRunner(object):
    """Executes a command"""

    def __init__(self, command):
        self._command = command

    @property
    def command(self):
        return self._command

    def run(self, sysargs=sys.argv, prog=None):
        parser = CommandArgumentParser(description=self.command.description, prog=prog,
            formatter_class=CommandArgumentFormatter)
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
                        if skwargs.has_key('silent'):
                            del skwargs['silent']
                            skwargs['help'] = argparse.SUPPRESS
                        subparser.add_argument(*sargs, **skwargs)
            else:
                if kwargs.has_key('silent'):
                    del kwargs['silent']
                    kwargs['help'] = argparse.SUPPRESS
                parser.add_argument(*args, **kwargs)
        args = parser.parse_args(sysargs)

        try:
            self.command.run(args)
        except CommandArgumentError as e:
            parser.error(e.message)


if __name__ == "__main__":
    CommandRunner(Command()).run()
