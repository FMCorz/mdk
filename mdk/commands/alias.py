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
from ..command import Command


class AliasCommand(Command):

    _arguments = [
        (
            ['action'],
            {
                'metavar': 'action',
                'help': 'the action to perform',
                'sub-commands':
                    {
                        'list': (
                            {
                                'help': 'list the aliases'
                            },
                            []
                        ),
                        'show': (
                            {
                                'help': 'display an alias'
                            },
                            [
                                (
                                    ['alias'],
                                    {
                                        'type': str,
                                        'metavar': 'alias',
                                        'default': None,
                                        'help': 'alias to display'
                                    }
                                )
                            ]
                        ),
                        'add': (
                            {
                                'help': 'adds an alias'
                            },
                            [
                                (
                                    ['alias'],
                                    {
                                        'type': str,
                                        'metavar': 'alias',
                                        'default': None,
                                        'help': 'alias name'
                                    }
                                ),
                                (
                                    ['definition'],
                                    {
                                        'type': str,
                                        'metavar': 'command',
                                        'default': None,
                                        'nargs': argparse.REMAINDER,
                                        'help': 'alias definition'
                                    }
                                )
                            ]
                        ),
                        'remove': (
                            {
                                'help': 'remove an alias'
                            },
                            [
                                (
                                    ['alias'],
                                    {
                                        'type': str,
                                        'metavar': 'alias',
                                        'default': None,
                                        'help': 'alias to remove'
                                    }
                                )
                            ]
                        ),
                        'set': (
                            {
                                'help': 'update/add an alias'
                            },
                            [
                                (
                                    ['alias'],
                                    {
                                        'type': str,
                                        'metavar': 'alias',
                                        'default': None,
                                        'help': 'alias name'
                                    }
                                ),
                                (
                                    ['definition'],
                                    {
                                        'type': str,
                                        'metavar': 'command',
                                        'default': None,
                                        'nargs': argparse.REMAINDER,
                                        'help': 'alias definition'
                                    }
                                )
                            ]
                        )
                    }
            }
        )
    ]
    _description = 'Manage your aliases'

    def run(self, args):
        if args.action == 'list':
            aliases = self.C.get('aliases')
            for alias, command in aliases.items():
                print '{0:<20}: {1}'.format(alias, command)

        elif args.action == 'show':
            alias = self.C.get('aliases.%s' % args.alias)
            if alias != None:
                print alias

        elif args.action == 'add':
            self.C.add('aliases.%s' % args.alias, ' '.join(args.definition))

        elif args.action == 'set':
            self.C.set('aliases.%s' % args.alias, ' '.join(args.definition))

        elif args.action == 'remove':
            self.C.remove('aliases.%s' % args.alias)
