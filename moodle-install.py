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

from lib import config, db, moodle, workplace
from lib.tools import debug

DB = db.DB
C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description='Install a Moodle instance')
parser.add_argument('-e', '--engine', action='store', choices=['mysqli', 'pgsql'], default=C('defaultEngine'), help='database engine to use', metavar='engine')
parser.add_argument('-f', '--fullname', action='store', help='full name of the instance', metavar='fullname')
parser.add_argument('-r', '--run', action='store', nargs='*', help='scripts to run after installation', metavar='run')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

name = args.name
engine = args.engine
fullname = args.fullname

M = Wp.resolve(name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

name = M.get('identifier')
dataDir = Wp.getPath(name, 'data')
if not os.path.isdir(dataDir):
	os.mkdir(dataDir, 0777)

kwargs = {
	'engine': engine,
	'fullname': fullname,
	'dataDir': dataDir
}
M.install(**kwargs)

if M.isInstalled():
    for script in args.run:
        debug('Running script \'%s\'' % (script))
        try:
            M.runScript(script)
        except Exception as e:
            debug('Error while running the script')
            debug(e)
