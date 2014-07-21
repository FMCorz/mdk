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

import logging
from ..command import Command


class InfoCommand(Command):

    _arguments = [
        (
            ['-e', '--edit'],
            {
                'dest': 'edit',
                'help': 'value to set to the variable (--var). This value will be set in the config file of the instance. Prepend the value with i: or b: to set as int or boolean. DO NOT use names used by MDK (identifier, stablebranch, ...).',
                'metavar': 'value',
                'nargs': '?'
            }
        ),
        (
            ['-i', '--integration'],
            {
                'action': 'store_true',
                'dest': 'integration',
                'help': 'used with --list, only display integration instances'
            }
        ),
        (
            ['-l', '--list'],
            {
                'action': 'store_true',
                'dest': 'list',
                'help': 'list the instances'
            }
        ),
        (
            ['-n', '--name-only'],
            {
                'action': 'store_true',
                'dest': 'nameonly',
                'help': 'used with --list, only display instances name'
            }
        ),
        (
            ['-s', '--stable'],
            {
                'action': 'store_true',
                'dest': 'stable',
                'help': 'used with --list, only display stable instances'
            }
        ),
        (
            ['-v', '--var'],
            {
                'default': None,
                'help': 'variable to output or edit',
                'metavar': 'var',
                'nargs': '?'
            }
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name',
                'nargs': '?'
            }
        )
    ]
    _description = 'Information about a Moodle instance'

    def run(self, args):
        # List the instances
        if args.list:
            if args.integration != False or args.stable != False:
                l = self.Wp.list(integration=args.integration, stable=args.stable)
            else:
                l = self.Wp.list()
            l.sort()
            for i in l:
                if not args.nameonly:
                    M = self.Wp.get(i)
                    print '{0:<25}'.format(i), M.get('release')
                else:
                    print i

        # Loading instance
        else:
            M = self.Wp.resolve(args.name)
            if not M:
                raise Exception('This is not a Moodle instance')

            # Printing/Editing variable.
            if args.var != None:
                # Edit a value.
                if args.edit != None:
                    val = args.edit
                    if val.startswith('b:'):
                        val = True if val[2:].lower() in ['1', 'true'] else False
                    elif val.startswith('i:'):
                        try:
                            val = int(val[2:])
                        except ValueError:
                            # Not a valid int, let's consider it a string.
                            pass
                    M.updateConfig(args.var, val)
                    logging.info('Set $CFG->%s to %s on %s' % (args.var, str(val), M.get('identifier')))
                else:
                    print M.get(args.var)

            # Printing info
            else:
                infos = M.info()
                for key in sorted(infos.keys()):
                    print '{0:<20}: {1}'.format(key, infos[key])
