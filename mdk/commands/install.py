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

import os
import logging
from .. import db
from ..command import Command
from ..tools import mkdir

DB = db.DB


class InstallCommand(Command):

    _description = 'Install a Moodle instance'

    def __init__(self, *args, **kwargs):
        super(InstallCommand, self).__init__(*args, **kwargs)
        self._arguments = [
            (
                ['-e', '--engine'],
                {
                'action': 'store',
                  'choices': ['mariadb', 'mysqli', 'pgsql'],
                  'default': self.C.get('defaultEngine'),
                  'help': 'database engine to use',
                  'metavar': 'engine'
                }
            ),
            (
                ['-f', '--fullname'],
                {
                    'action': 'store',
                    'help': 'full name of the instance',
                    'metavar': 'fullname'
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
                ['name'],
                {
                    'default': None,
                    'help': 'name of the instance',
                    'metavar': 'name',
                    'nargs': '?'
                })
        ]

    def run(self, args):

        name = args.name
        engine = args.engine
        fullname = args.fullname

        M = self.Wp.resolve(name)
        if not M:
            raise Exception('This is not a Moodle instance')

        name = M.get('identifier')
        dataDir = self.Wp.getPath(name, 'data')
        if not os.path.isdir(dataDir):
            mkdir(dataDir, 0777)

        kwargs = {
            'engine': engine,
            'fullname': fullname,
            'dataDir': dataDir,
            'wwwroot': self.Wp.getUrl(name)
        }
        M.install(**kwargs)

        # Running scripts
        if M.isInstalled() and type(args.run) == list:
            for script in args.run:
                logging.info('Running script \'%s\'' % (script))
                try:
                    M.runScript(script)
                except Exception as e:
                    logging.warning('Error while running the script: %s' % e)
