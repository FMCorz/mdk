#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import json
import time
from distutils.dir_util import copy_tree
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description='Backup a Moodle instance')
parser.add_argument('-l', '--list', action='store_true', help='list the backups', dest='list')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

name = args.name
backupdir = os.path.join(C('dirs.moodle'), 'backup')

# List the backups
if args.list:
    dirs = os.listdir(backupdir)
    backups = {}

    for d in dirs:
    	path = os.path.join(backupdir, d)
    	jsonfile = os.path.join(path, 'info.json')
        if d == '.' or d == '..': continue
        if not os.path.isdir(path): continue
        if not os.path.isfile(jsonfile): continue
        infos = json.load(open(jsonfile, 'r'))
        backups[d] = infos

    for name, info in backups.iteritems():
    	backuptime = time.ctime(info['backup_time'])
    	print '{0:<25}: {1:<30} {2}'.format(name, info['release'], backuptime)

    sys.exit(0)

# Resolve the instance
M = Wp.resolve(name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

if M.get('dbtype') != 'mysqli':
	debug('Does not support backup for this DB engine %s yet, sorry!' % M.get('dbtype'))

debug('Backuping %s' % name)
now = int(time.time())
backup_identifier = '%s_%s' % (name, now)

# Copy whole directory, shutil will create topath
topath = os.path.join(backupdir, backup_identifier)
path = Wp.getPath(name)
try:
	debug('Copying instance directory')
	copy_tree(path, topath, preserve_symlinks = 1)
except Exception as e:
	debug('Error while backuping directory %s to %s' % (path, topath))
	debug(e)
	sys.exit(1)

# Dump the whole database
if M.isInstalled():
    debug('Dumping database')
    dumpto = os.path.join(topath, 'dump.sql')
    fd = open(dumpto, 'w')
    M.dbo().selectdb(M.get('dbname'))
    M.dbo().dump(fd)
else:
    debug('Instance not installed. Do not dump database.')

# Create a JSON file containing all known information
debug('Saving instance information')
jsonto = os.path.join(topath, 'info.json')
info = M.info()
info['backup_identifier'] = backup_identifier
info['backup_time'] = now
json.dump(info, open(jsonto, 'w'), sort_keys = True, indent = 4)

debug('Done.')
