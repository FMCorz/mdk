#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import re

from lib import config, db, moodle, workplace
from lib.tools import debug, yesOrNo

DB = db.DB
C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description='Creates a new instance of Moodle')
parser.add_argument('-t', '--integration', action='store_true', help='create an instance from integration')
parser.add_argument('-i', '--install', action='store_true', help='launch the installation script after creating the instance', dest='install')
parser.add_argument('-v', '--version', action='store', choices=[ str(x) for x in range(13, C('masterBranch')) ] + ['master'], default='master', help='version of Moodle', metavar='version')
parser.add_argument('-s', '--suffix', action='store', help='suffix for the instance name', metavar='suffix')
parser.add_argument('-e', '--engine', action='store', choices=['mysqli', 'pgsql'], default=C('defaultEngine'), help='database engine to use', metavar='engine')
args = parser.parse_args()

engine = args.engine
version = args.version
name = Wp.generateInstanceName(version, integration = args.integration, suffix = args.suffix)

# Wording version
versionNice = version
if version == 'master':
	versionNice = C('wording.master')

# Generating names
if args.integration:
	fullname = C('wording.integration') + ' ' + versionNice + ' ' + C('wording.%s' % engine)
else:
	fullname = C('wording.stable') + ' ' + versionNice + ' ' + C('wording.%s' % engine)

# Append the suffix
if args.suffix:
	fullname += ' ' + args.suffix.replace('-', ' ').replace('_', ' ').title()

# Create the instance
debug('Creating instance %s...' % name)
kwargs = {
	'name': name,
	'version': version,
	'integration': args.integration,
	'useCacheAsRemote': C('useCacheAsRemote')
}
try:
	M = Wp.create(**kwargs)
except Exception as e:
	debug(e)
	sys.exit(1)

# Run the install script
if args.install:

	# Checking database
	dbname = re.sub(r'[^a-zA-Z0-9]', '', name).lower()[:28]
	db = DB(engine, C('db.%s' % engine))
	dropDb = False
	if db.dbexists(dbname):
		debug('Database already exists (%s)' % dbname)
		dropDb = yesOrNo('Do you want to remove it?')

	# Install
	kwargs = {
		'engine': engine,
		'dbname': dbname,
		'dropDb': dropDb,
		'fullname': fullname,
		'dataDir': Wp.getPath(name, 'data')
	}
	M.install(**kwargs)

debug('Process complete!')
