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
import os
import argparse
from lib import moodle, workplace
from lib.tools import debug, process
from lib.config import Conf

C = Conf()

# Arguments
parser = argparse.ArgumentParser(description='Initialize PHPUnit')
parser.add_argument('-r', '--run', action='store_true', help='also run the tests')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

Wp = workplace.Workplace(C.get('dirs.storage'))

# Loading instance
M = Wp.resolve(args.name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

# Check if installed
if not M.get('installed'):
    debug('This instance needs to be installed first')
    sys.exit(1)

# Run cli
try:
    M.initPHPUnit()
    debug('PHPUnit ready!')
    if args.run:
        debug('Running PHPUnit')
        process('phpunit', M.path, None, None)
except Exception as e:
    debug(e)
    sys.exit(1)
