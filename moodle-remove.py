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

import os
import sys
import argparse

from lib import config, tools, workplace
from lib.tools import debug

C = config.Conf().get

# Arguments
parser = argparse.ArgumentParser(description='Completely remove an instance')
parser.add_argument('name', help='name of the instance')
parser.add_argument('-y', action='store_true', help='do not ask for confirmation', dest='do')
args = parser.parse_args()

Wp = workplace.Workplace()
try:
	M = Wp.get(args.name)
except:
	debug('This is not a Moodle instance')
	sys.exit(1)

if not args.do:
	confirm = raw_input('Are you sure? (Y/n) ')
	if confirm != 'Y':
		debug('Exiting...')
		sys.exit(0)

debug('Removing %s...' % args.name)
try:
    Wp.delete(args.name)
except OSError:
    debug('Error while deleting the instance.')
    debug('This is probably a permission issue.')
    debug('Run: sudo chmod -R 0777 %s' % Wp.getPath(args.name))
    sys.exit(1)

debug('Instance removed')
