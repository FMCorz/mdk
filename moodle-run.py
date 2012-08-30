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
parser = argparse.ArgumentParser(description='Run a script on a Moodle instance')
parser.add_argument('script', metavar='script', help='the name of the script to run on the instance')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

M = Wp.resolve(args.name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

try:
	debug('Running \'%s\' on \'%s\'' % (args.script, M.get('identifier')))
	M.runScript(args.script, stderr=None, stdout=None)
except Exception as e:
	debug(e)

debug('Done.')
