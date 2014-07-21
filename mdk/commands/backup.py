#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2013 Frédéric Massart - FMCorz.net

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

import time
import logging
from distutils.errors import DistutilsFileError
from .. import backup
from ..command import Command
from ..exceptions import *


class BackupCommand(Command):

    _arguments = [
        (
            ['-i', '--info'],
            {
                'dest': 'info',
                'help': 'lists all the information about a backup',
                'metavar': 'backup'
            }
        ),
        (
            ['-l', '--list'],
            {
                'action': 'store_true',
                'dest': 'list',
                'help': 'list the backups'
            },
        ),
        (
            ['-r', '--restore'],
            {
                'dest': 'restore',
                'help': 'restore a backup',
                'metavar': 'backup'
            }
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'nargs': '?'
            }
        )
    ]

    _description = 'Backup a Moodle instance'

    def run(self, args):
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
                raise Exception('This is not a valid backup')

            # Restore process
            B = BackupManager.get(name)
            infos = B.infos
            print 'Displaying information about %s' % name
            for key in sorted(infos.keys()):
                print '{0:<20}: {1}'.format(key, infos[key])

        # Restore
        elif args.restore:
            name = args.restore

            # Resolve the backup
            if not name or not BackupManager.exists(name):
                raise Exception('This is not a valid backup')

            # Restore process
            B = BackupManager.get(name)

            try:
                M = B.restore()
            except BackupDirectoryExistsException:
                raise Exception('Cannot restore an instance on an existing directory. Please remove %s first.' % B.get('identifier') +
                    'Run: moodle remove %s' % B.get('identifier'))
            except BackupDBExistsException:
                raise Exception('The database %s already exists. Please remove it first.' % B.get('dbname') +
                    'This command could help: moodle remove %s' % B.get('identifier'))

            # Loads M object and display information
            logging.info('')
            logging.info('Restored instance information')
            logging.info('')
            infos = M.info()
            for key in sorted(infos.keys()):
                print '{0:<20}: {1}'.format(key, infos[key])
            logging.info('')

            logging.info('Done.')

        # Backup the instance
        else:
            M = self.Wp.resolve(name)
            if not M:
                raise Exception('This is not a Moodle instance')

            try:
                BackupManager.create(M)
            except BackupDBEngineNotSupported:
                raise Exception('Does not support backup for the DB engine %s yet, sorry!' % M.get('dbtype'))

            except DistutilsFileError:
                raise Exception('Error while copying files. Check the permissions on the data directory.' +
                    'Or run: sudo chmod -R 0777 %s' % M.get('dataroot'))

            logging.info('Done.')
