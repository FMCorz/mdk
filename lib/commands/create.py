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

import sys
import re

from lib.db import DB
from lib.command import Command
from lib.tools import debug, yesOrNo


class CreateCommand(Command):

    _description = 'Creates a new instance of Moodle'

    def __init__(self, *args, **kwargs):
        super(CreateCommand, self).__init__(*args, **kwargs)
        self._arguments = [
            (
                ['-e', '--engine'],
                {
                    'action': 'store',
                    'choices': ['mysqli', 'pgsql'],
                    'default': self.C.get('defaultEngine'),
                    'help': 'database engine to use',
                    'metavar': 'engine'
                }
            ),
            (
                ['-i', '--install'],
                {
                    'action': 'store_true',
                    'dest': 'install',
                    'help': 'launch the installation script after creating the instance'
                }
            ),
            (
                ['-t', '--integration'],
                {
                    'action': 'store_true',
                    'help': 'create an instance from integration'
                }
            ),
            (
                ['-r', '--run'],
                {
                    'action': 'store',
                    'help': 'scripts to run after installation',
                    'metavar': 'run',
                    'nargs': '*'
                }
            ),
            (
                ['-s', '--suffix'],
                {
                    'action': 'store',
                    'help': 'suffix for the instance name',
                    'metavar': 'suffix'
                }
            ),
            (
                ['-v', '--version'],
                {
                    'choices': [str(x) for x in range(13, int(self.C.get('masterBranch')))] + ['master'],
                    'default': 'master',
                    'help': 'version of Moodle',
                    'metavar': 'version'
                }
            ),
        ]

    def run(self, args):

        engine = args.engine
        version = args.version
        name = self.Wp.generateInstanceName(version, integration=args.integration, suffix=args.suffix)

        # Wording version
        versionNice = version
        if version == 'master':
            versionNice = self.C.get('wording.master')

        # Generating names
        if args.integration:
            fullname = self.C.get('wording.integration') + ' ' + versionNice + ' ' + self.C.get('wording.%s' % engine)
        else:
            fullname = self.C.get('wording.stable') + ' ' + versionNice + ' ' + self.C.get('wording.%s' % engine)

        # Append the suffix
        if args.suffix:
            fullname += ' ' + args.suffix.replace('-', ' ').replace('_', ' ').title()

        # Create the instance
        debug('Creating instance %s...' % name)
        kwargs = {
            'name': name,
            'version': version,
            'integration': args.integration,
            'useCacheAsRemote': self.C.get('useCacheAsRemote')
        }
        try:
            M = self.Wp.create(**kwargs)
        except Exception as e:
            debug(e)
            sys.exit(1)

        # Run the install script
        if args.install:

            # Checking database
            dbname = re.sub(r'[^a-zA-Z0-9]', '', name).lower()[:28]
            db = DB(engine, self.C.get('db.%s' % engine))
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
                'dataDir': self.Wp.getPath(name, 'data')
            }
            M.install(**kwargs)

            # Running scripts
            if M.isInstalled() and type(args.run) == list:
                for script in args.run:
                    debug('Running script \'%s\'' % (script))
                    try:
                        M.runScript(script)
                    except Exception as e:
                        debug('Error while running the script')
                        debug(e)

        debug('Process complete!')
