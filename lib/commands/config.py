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

from lib.command import Command
from lib.tools import debug


class ConfigCommand(Command):

    _arguments = [
        (
            ['action'],
            {
                'help': 'the action to perform',
                'metavar': 'action',
                'sub-commands': {
                    'flatlist': (
                        {
                            'help': 'flat list of the settings'
                        },
                        []
                    ),
                    'list': (
                        {
                            'help': 'list the settings'
                        },
                        []
                    ),
                    'show': (
                        {
                            'help': 'display one setting'
                        },
                        [
                            (
                                ['setting'],
                                {
                                    'metavar': 'setting',
                                    'help': 'setting to display'
                                }
                            )
                        ]
                    ),
                    'set': (
                        {
                            'help': 'set the value of a setting'
                        },
                        [
                            (
                                ['setting'],
                                {
                                    'metavar': 'setting',
                                    'help': 'setting to edit'
                                }
                            ),
                            (
                                ['value'],
                                {
                                    'metavar': 'value',
                                    'help': 'value to set'
                                }
                            )
                        ]
                    )
                }
            }
        )
    ]
    _description = 'Manage your configuration'

    def run(self, args):
        if args.action == 'list':
            def show_list(settings, ident):
                for name, setting in settings.items():
                    if type(setting) != dict:
                        print u'{0:<20}: {1}'.format(u' ' * ident + name, setting)
                    else:
                        print u' ' * ident + '[%s]' % name
                        show_list(setting, ident + 2)
            show_list(self.C.get(), 0)

        elif args.action == 'flatlist':
            def show_list(settings, parent=''):
                for name, setting in settings.items():
                    if type(setting) != dict:
                        print u'%s: %s' % (parent + name, setting)
                    else:
                        show_list(setting, parent + name + u'.')
            show_list(self.C.get())

        elif args.action == 'show':
            setting = self.C.get(args.setting)
            if setting != None:
                debug(setting)

        elif args.action == 'set':
            setting = args.setting
            val = args.value
            if val.startswith('b:'):
                val = True if val[2:].lower() in ['1', 'true'] else False
            elif val.startswith('i:'):
                try:
                    val = int(val[2:])
                except ValueError:
                    # Not a valid int, let's consider it a string.
                    pass
            self.C.set(setting, val)
