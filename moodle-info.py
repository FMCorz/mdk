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
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description='Display information about a Moodle instance')
parser.add_argument('-l', '--list', action='store_true', help='list the instances', dest='list')
parser.add_argument('-i', '--integration', action='store_true', help='used with --list, only display integration instances', dest='integration')
parser.add_argument('-s', '--stable', action='store_true', help='used with --list, only display stable instances', dest='stable')
parser.add_argument('-n', '--name-only', action='store_true', help='used with --list, only display instances name', dest='nameonly')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
parser.add_argument('var', metavar='var', default=None, nargs='?', help='variable to output')
args = parser.parse_args()

# List the instances
if args.list:
	if args.integration != False or args.stable != False:
		l = Wp.list(integration = args.integration, stable = args.stable)
	else:
		l = Wp.list()
	l.sort()
	for i in l:
		M = Wp.get(i)
		if not args.nameonly:
			print '{0:<25}'.format(i), M.get('release')
		else:
			print i

# Loading instance
else:
	M = Wp.resolve(args.name)
	if not M:
	    debug('This is not a Moodle instance')
	    sys.exit(1)

	# Printing variable
	if args.var != None:
		print M.get(args.var)

	# Printing info
	else:
		for key, info in M.info().items():
			print '{0:<20}: {1}'.format(key, info)
