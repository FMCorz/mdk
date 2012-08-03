#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
parser.add_argument('-y', '--non-interactive', action='store_true', help='non-interactive mode', dest='noninteractive')
parser.add_argument('-f', '--fullname', action='store', help='full name of the instance')
parser.add_argument('name', metavar='name', help='name of the instance')
args = parser.parse_args()

name = args.name
engine = args.engine
fullname = args.fullname

if not Wp.isMoodle(name):
	debug('Instance %s does not exist. Exiting...' % name)
	sys.exit(1)

dataDir = Wp.getPath(name, 'data')
if not os.path.isdir(dataDir):
	os.mkdir(dataDir, 0777)

M = Wp.get(name)
kwargs = {
	'engine': engine,
	'fullname': fullname,
	'dataDir': dataDir
}
M.install(**kwargs)
