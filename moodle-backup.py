#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import json
import time
from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError
from lib import config, workplace, moodle, tools, backup
from lib.exceptions import *
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description='Backup a Moodle instance')
parser.add_argument('-l', '--list', action='store_true', help='list the backups', dest='list')
parser.add_argument('-i', '--info', metavar='backup', help='lists all the information about a backup', dest='info')
parser.add_argument('-r', '--restore', help='restore a backup', metavar='backup', dest='restore')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

name = args.name
BackupManager = backup.BackupManager()

# List the backups
if args.list:
    backups = BackupManager.list()
    for key in sorted(backups.keys()):
        B = backups[key]
        backuptime = time.ctime(B.get('backup_time'))
        print '{0:<25}: {1:<30} {2}'.format(key, B.get('release'), backuptime)

# Displays backup information
elif args.info:
    name = args.info

    # Resolve the backup
    if not name or not BackupManager.exists(name):
        debug('This is not a valid backup')
        sys.exit(1)

    # Restore process
    B = BackupManager.get(name)
    infos = B.infos
    debug('Displaying information about %s' % name)
    for key in sorted(infos.keys()):
        debug('{0:<20}: {1}'.format(key, infos[key]))

# Restore
elif args.restore:
    name = args.restore

    # Resolve the backup
    if not name or not BackupManager.exists(name):
        debug('This is not a valid backup')
        sys.exit(1)

    # Restore process
    B = BackupManager.get(name)

    try:
        M = B.restore()
    except BackupDirectoryExistsException as e:
        debug('Cannot restore an instance on an existing directory. Please remove %s first.' % B.get('identifier'))
        debug('Run: moodle remove %s' % B.get('identifier'))
        sys.exit(1)
    except BackupDBExistsException as e:
        debug('The database %s already exists. Please remove it first.' % B.get('dbname'))
        debug('This command could help: moodle remove %s' % B.get('identifier'))
        sys.exit(1)

    # Loads M object and display information
    debug('')
    debug('Restored instance information')
    debug('')
    infos = M.info()
    for key in sorted(infos.keys()):
        print '{0:<20}: {1}'.format(key, infos[key])
    debug('')

    debug('Done.')

# Backup the instance
else:
    M = Wp.resolve(name)
    if not M:
        debug('This is not a Moodle instance')
        sys.exit(1)

    try:
        BackupManager.create(M)
    except BackupDBEngineNotSupported as e:
        debug('Does not support backup for the DB engine %s yet, sorry!' % M.get('dbtype'))
        sys.exit(1)
    except DistutilsFileError as e:
        debug('Error while copying files. Check the permissions on the data directory.')
        debug('Or run: sudo chmod -R 0777 %s' % M.get('dataroot'))
        sys.exit(1)

    debug('Done.')
