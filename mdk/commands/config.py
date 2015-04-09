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
import re
from ..command import Command
from ..tools import launchEditor, yesOrNo
from ..config import ConfigObject, ConfigFileCouldNotBeLoaded


class ConfigCommand(Command):

    _arguments = [
        (
            ['action'],
            {
                'help': 'the action to perform',
                'metavar': 'action',
                'sub-commands': {
                    'edit': (
                        {
                            'help': 'opens the config file in an editor'
                        },
                        []
                    ),
                    'flatlist': (
                        {
                            'help': 'flat list of the settings'
                        },
                        [
                            (
                                ['-g', '--grep'],
                                {
                                    'metavar': 'string',
                                    'help': 'filter results using regular expressions'
                                }
                            ),
                        ]
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
                                    'default': '',
                                    'metavar': 'value',
                                    'nargs': '?',
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

    def dictDisplay(self, data, ident=0):
        for name in sorted(data.keys()):
            setting = data[name]
            if type(setting) != dict:
                print u'{0:<20}: {1}'.format(u' ' * ident + name, setting)
            else:
                print u' ' * ident + '[%s]' % name
                self.dictDisplay(setting, ident + 2)

    def flatDisplay(self, data, parent='', regex=None):
        for name in sorted(data.keys()):
            setting = data[name]
            if type(setting) != dict:
                if regex and not regex.search(parent + name):
                    continue
                print u'%s: %s' % (parent + name, setting)
            else:
                self.flatDisplay(setting, parent=parent + name + u'.', regex=regex)

    def run(self, args):
        if args.action == 'list':
            self.dictDisplay(self.C.get(), 0)

        elif args.action == 'edit':
            f = self.C.userFile
            success = None

            while True:
                tmpfile = launchEditor(filepath=f, suffix='.json')
                co = ConfigObject()
                try:
                    co.loadFromFile(tmpfile)
                except ConfigFileCouldNotBeLoaded:
                    success = False
                    logging.error('I could not load the file, you probably screwed up the JSON...')
                    if yesOrNo('Would you like to continue editing? If not the changes will be discarded.'):
                        f = tmpfile
                        continue
                    else:
                        break
                else:
                    success = True
                    break

            if success:
                with open(tmpfile, 'r') as new:
                    with open(self.C.userFile, 'w') as current:
                        current.write(new.read())

        elif args.action == 'flatlist':
            regex = None
            if args.grep:
                regex = re.compile(args.grep, re.I)
            self.flatDisplay(self.C.get(), regex=regex)

        elif args.action == 'show':
            setting = self.C.get(args.setting)
            if setting != None:
                if type(setting) == dict:
                    self.flatDisplay(setting, args.setting + u'.')
                else:
                    print setting

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
