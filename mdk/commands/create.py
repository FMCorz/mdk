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

import re
import logging

from ..db import DB
from ..command import Command
from ..tools import yesOrNo
from ..exceptions import CreateException, InstallException


class CreateCommand(Command):

    _description = 'Creates new instances of Moodle'

    def __init__(self, *args, **kwargs):
        super(CreateCommand, self).__init__(*args, **kwargs)
        self._arguments = [
            (
                ['-i', '--install'],
                {
                    'action': 'store_true',
                    'dest': 'install',
                    'help': 'launch the installation script after creating the instance'
                }
            ),
            (
                ['-e', '--engine'],
                {
                    'action': 'store',
                    'choices': ['mariadb', 'mysqli', 'pgsql'],
                    'default': self.C.get('defaultEngine'),
                    'help': 'database engine to install the instance on, use with --install',
                    'metavar': 'engine'
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
                ['-n', '--identifier'],
                {
                    'action': 'store',
                    'default': None,
                    'help': 'use this identifier instead of generating one. The flag --suffix will be used. ' +
                        'Do not use when creating multiple versions at once',
                    'metavar': 'name',
                }
            ),
            (
                ['-s', '--suffix'],
                {
                    'action': 'store',
                    'default': [None],
                    'help': 'suffixes for the instance name',
                    'metavar': 'suffix',
                    'nargs': '*'
                }
            ),
            (
                ['-v', '--version'],
                {
                    'choices': [str(x) for x in range(13, int(self.C.get('masterBranch')))] + ['master'],
                    'default': ['master'],
                    'help': 'version of Moodle',
                    'metavar': 'version',
                    'nargs': '*'
                }
            ),
        ]

    def run(self, args):

        engine = args.engine
        versions = args.version
        suffixes = args.suffix
        install = args.install

        # Throw an error when --engine is used without --install. The code is currently commented out
        # because as --engine has a default value, it will always be set, and so it becomes impossible
        # to create an instance without installing it. I cannot think about a clean fix yet. Removing
        # the default value will cause --help not to output the default as it should... Let's put more
        # thoughts into this and perhaps use argument groups.
        # if engine and not install:
            # self.argumentError('--engine can only be used with --install.')

        for version in versions:
            for suffix in suffixes:
                arguments = {
                    'version': version,
                    'suffix': suffix,
                    'engine': engine,
                    'integration': args.integration,
                    'identifier': args.identifier,
                    'install': install,
                    'run': args.run
                }
                self.do(arguments)
                logging.info('')

        logging.info('Process complete!')

    def do(self, args):
        """Proceeds to the creation of an instance"""

        # TODO Remove these ugly lines, but I'm lazy to rewrite the variables in this method...
        class Bunch:
            __init__ = lambda self, **kw: setattr(self, '__dict__', kw)
        args = Bunch(**args)

        engine = args.engine
        version = args.version
        name = self.Wp.generateInstanceName(version, integration=args.integration, suffix=args.suffix, identifier=args.identifier)

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
        logging.info('Creating instance %s...' % name)
        kwargs = {
            'name': name,
            'version': version,
            'integration': args.integration
        }
        try:
            M = self.Wp.create(**kwargs)
        except CreateException as e:
            logging.error('Error creating %s:\n  %s' % (name, e))
            return False
        except Exception as e:
            logging.exception('Error creating %s:\n  %s' % (name, e))
            return False

        # Run the install script
        if args.install:

            # Checking database
            dbname = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
            prefixDbname = self.C.get('db.namePrefix')
            if prefixDbname:
                dbname = prefixDbname + dbname
            dbname = dbname[:28]
            db = DB(engine, self.C.get('db.%s' % engine))
            dropDb = False
            if db.dbexists(dbname):
                logging.info('Database already exists (%s)' % dbname)
                dropDb = yesOrNo('Do you want to remove it?')

            # Install
            kwargs = {
                'engine': engine,
                'dbname': dbname,
                'dropDb': dropDb,
                'fullname': fullname,
                'dataDir': self.Wp.getPath(name, 'data'),
                'wwwroot': self.Wp.getUrl(name)
            }
            try:
                M.install(**kwargs)
            except InstallException as e:
                logging.warning('Error while installing %s:\n  %s' % (name, e))
                return False
            except Exception as e:
                logging.exception('Error while installing %s:\n  %s' % (name, e))
                return False

            # Running scripts
            if M.isInstalled() and type(args.run) == list:
                for script in args.run:
                    logging.info('Running script \'%s\'' % (script))
                    try:
                        M.runScript(script)
                    except Exception as e:
                        logging.warning('Error while running the script \'%s\':\  %s' % (script, e))
