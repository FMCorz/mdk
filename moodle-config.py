#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2012 Frédéric Massart - FMCorz.net

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

import sys
import argparse
from lib.tools import debug
from lib.config import C

# Arguments
parser = argparse.ArgumentParser(description='Manage your configuration')
parser.add_argument('command', metavar='command', choices=['flatlist', 'list', 'show', 'set'], help='the action to perform')
parser.add_argument('arguments', metavar='arguments', default=None, nargs='*', help='arguments for the command')
args = parser.parse_args()

if args.command == 'list':
    def show_list(settings, ident):
        for name, setting in settings.items():
            if type(setting) != dict:
                print u'{0:<20}: {1}'.format(u' ' * ident + name, setting)
            else:
                print u' ' * ident + '[%s]' % name
                show_list(setting, ident + 2)
    show_list(C.get(), 0)

elif args.command == 'flatlist':
    def show_list(settings, parent = ''):
        for name, setting in settings.items():
            if type(setting) != dict:
                print u'%s: %s' % (parent + name, setting)
            else:
                show_list(setting, parent + name + u'.')
    show_list(C.get())

elif args.command == 'show':
    if len(args.arguments) != 1:
        debug('Too few/many arguments. One needed: moodle config show settingName')
        sys.exit(1)
    setting = C.get(args.arguments[0])
    if setting != None:
        debug(setting)

elif args.command == 'set':
    if len(args.arguments) < 2:
        debug('Too few arguments. Two needed: moodle config set settingName value')
        sys.exit(1)
    setting = args.arguments[0]
    value = u' '.join(args.arguments[1:])
    C.set(setting, value)
