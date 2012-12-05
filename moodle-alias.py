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
from lib.config import Conf

C = Conf()

# Arguments
parser = argparse.ArgumentParser(description='Manage your aliases')
parser.add_argument('command', metavar='command', choices=['list', 'show', 'add', 'remove'], help='the action to perform')
parser.add_argument('arguments', type=str, metavar='arguments', default=None, nargs=argparse.REMAINDER, help='arguments for the command')
args = parser.parse_args()

if args.command == 'list':
    aliases = C.get('aliases')
    for alias, command in aliases.items():
        print '{0:<20}: {1}'.format(alias, command)

elif args.command == 'show':
    if len(args.arguments) != 1:
        debug('Too few/many arguments. One needed: moodle alias show aliasName')
        sys.exit(1)
    alias = C.get('aliases.%s' % args.arguments[0])
    if alias != None:
        debug(alias)

elif args.command == 'add':
    if len(args.arguments) < 2:
        debug('Too few/many arguments. Two needed: moodle alias add aliasName Command To Perform')
        sys.exit(1)
    alias = args.arguments[0]
    command = ' '.join(args.arguments[1:])
    C.add('aliases.%s' % alias, command)

elif args.command == 'remove':
    if len(args.arguments) != 1:
        debug('Too few/many arguments. One needed: moodle alias remove aliasName')
        sys.exit(1)
    alias = args.arguments[0]
    C.remove('aliases.%s' % alias)
