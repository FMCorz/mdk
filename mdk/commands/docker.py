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
import sys
import logging
import subprocess
import re
import json
import shutil
from ..git import Git
from ..config import Conf
from ..command import Command
from ..exceptions import UpgradeNotAllowed
from ..tools import process

C = Conf()


class DockerCommand(Command):

    _arguments = [
        (
            ['--update'],
            {
                'action': 'store_true',
                'help': 'Update the moodle-docker project.'
            },
        ),
        (
            ['action'],
            {
                'metavar': 'action',
                'help': 'the action to perform',
                'sub-commands': {
                    'create': ({
                        'help': 'create a new docker variant'
                    }, [
                        (
                            ['-l', '--label'],
                            {
                                'action': 'store',
                                'default': None,
                                'help': 'a label for this variant',
                            },
                        ),
                        (
                            ['-d', '--db'],
                            {
                                'action': 'store',
                                'choices': ['mariadb', 'mysql', 'mssql', 'oracle', 'pgsql'],
                                'default': 'pgsql',
                                'help': 'database to use',
                                'metavar': 'db'
                            },
                        ),
                        (
                            ['-v', '--db-version'],
                            {
                                'action': 'store',
                                'default': None,
                                'help': 'database version to use',
                                'dest': 'dbversion',
                                'metavar': 'dbversion'
                            },
                        ),
                        (
                            ['-p', '--php'],
                            {
                                'action': 'store',
                                'choices': ['5.6', '7.0', '7.1', '7.2', '7.3', '7.4', '8.0', '8.1', '8.2'],
                                'default': None,
                                'help': 'PHP version to use',
                                'metavar': 'php'
                            },
                        ),
                        (
                            ['-P', '--port'],
                            {
                                'action': 'store',
                                'default': None,
                                'help': 'port number to use',
                                'metavar': 'port'
                            },
                        ),
                        (['name'], {
                            'default': None,
                            'help': 'name of the instance to work on',
                            'metavar': 'name',
                            'nargs': '?'
                        }),
                    ]),
                    'remove': ({
                        'help': 'remove the docker variant'
                    }, [
                        (
                            ['-l', '--label'],
                            {
                                'action': 'store',
                                'default': None,
                                'help': 'the label of the variant',
                            },
                        ),
                        (['name'], {
                            'default': None,
                            'help': 'name of the instance to work on',
                            'metavar': 'name',
                            'nargs': '?'
                        }),
                    ]),
                    'start': ({
                        'help': 'start the docker variant',
                        'aliases': ['up']
                    }, [
                        (
                            ['-l', '--label'],
                            {
                                'action': 'store',
                                'default': None,
                                'help': 'a label for this variant',
                            },
                        ),
                        (['name'], {
                            'default': None,
                            'help': 'name of the instance to work on',
                            'metavar': 'name',
                            'nargs': '?'
                        }),
                    ]),
                    'stop': ({
                        'help': 'stop the docker variant',
                        'aliases': ['down']
                    }, [
                        (
                            ['-l', '--label'],
                            {
                                'action': 'store',
                                'default': None,
                                'help': 'a label for this variant',
                            },
                        ),
                        (['name'], {
                            'default': None,
                            'help': 'name of the instance to work on',
                            'metavar': 'name',
                            'nargs': '?'
                        }),
                    ]),
                    'teardown': ({
                        'help': 'remove the docker instances'
                    }, [
                        (
                            ['-k', '--keep-volumes'],
                            {
                                'help': 'whether to keep the volumes',
                            },
                        ),
                        (
                            ['-l', '--label'],
                            {
                                'action': 'store',
                                'default': None,
                                'help': 'a label for this variant',
                            },
                        ),
                        (['name'], {
                            'default': None,
                            'help': 'name of the instance to work on',
                            'metavar': 'name',
                            'nargs': '?'
                        }),
                    ]),
                }
            },
        ),
    ]
    _description = 'Start the services of an instance'

    def run(self, args):
        if args.update:
            self.Wp.getMoodleDockerKnowAbout().update()

        if 'action' not in args:
            return

        identifier, variant = self.Wp.resolveIdentifierAndVariant(args.name)
        name = f'{identifier}.{variant}' if variant else identifier

        if not self.Wp.isMoodleInDocker(identifier):
            self.argumentError('The instance is not setup to use Docker.')

        if args.action == 'create':
            self.create(identifier, args)
            return

        M = self.Wp.get(name)
        if args.action == 'start':
            self.start(M, args)
        elif args.action == 'stop':
            self.stop(M, args)
        elif args.action == 'remove':
            self.remove(M, args)
        elif args.action == 'teardown':
            self.teardown(M, args)

    def create(self, identifier, args):
        data = self._get_docker_metadata(identifier)

        # Validate the label.
        label = args.label
        labels = set([v.get('label') for v in data.get('variants')])
        if label is not None and re.search(label, r'[^a-z0-9-]') is not None:
            self.argumentError('Invalid --label value, only lowercase letters, numbers and hyphens are allowed.')
        elif label in labels:
            if not label:
                self.argumentError('A default variant already exists, use --label.')
            self.argumentError('The variant already exists, please use another one.')

        projectprefix = C.get('moodle-docker.projectNamePrefix') or ''
        projectname = f'{projectprefix}{identifier}' + ('-' + label if label else '')
        db = args.db
        dbversion = args.dbversion
        php = args.php
        webhost = 'localhost'
        webport = args.port

        variant = {
            'label': args.label,
            'projectname': projectname,
            'env': {
                'MOODLE_DOCKER_DB': db,
                'MOODLE_DOCKER_DB_VERSION': dbversion,
                'MOODLE_DOCKER_PHP_VERSION': php,
                'MOODLE_DOCKER_WEB_HOST': webhost,
                'MOODLE_DOCKER_WEB_PORT': webport,
            }
        }
        data['variants'].append(variant)

        self._save_docker_metadata(identifier, data)
        logging.info('New variant added')

        M = self.Wp.get(f'{identifier}.{args.label}' if args.label else identifier)
        logging.info('Starting containers')
        self._execute_docker_compose(M, variant, ['up', '-d'])
        logging.info('Containers started')

    def remove(self, M, args):
        variant = self._get_docker_variant(M.get('identifier'), args.label)

        if self._has_containers(M, variant):
            logging.info('Removing the containers, networks and volumes')
            self._execute_docker_compose(M, variant, ['rm', '-s', '-v', '-f'])

        data = self._get_docker_metadata(M.get('identifier'))
        data['variants'] = [v for v in data['variants'] if v['label'] != variant['label']]
        self._save_docker_metadata(M.get('identifier'), data)
        logging.info('Variant removed')

    def start(self, M, args):
        variant = self._get_docker_variant(M.get('identifier'), args.label)
        logging.info('Starting the containers')
        self._execute_docker_compose(M, variant, ['up', '-d'])

    def stop(self, M, args):
        variant = self._get_docker_variant(M.get('identifier'), args.label)
        logging.info('Stopping the containers')
        self._execute_docker_compose(M, variant, ['stop'])

    def teardown(self, M, args):
        variant = self._get_docker_variant(M.get('identifier'), args.label)

        items = 'containers and networks'
        if not args.keep_volumes:
            items = 'containers, networks and volumes'
        logging.info('Removing the %s', items)

        self._execute_docker_compose(M, variant, ['down'] + ([] if args.keep_volumes else ['-v']))

    def _execute_docker_compose(self, M, variant, command: list, stdout=None):
        return process(['/home/fmc/code/clones/moodle-docker/bin/moodle-docker-compose'] + command,
                       cwd='/home/fmc/code/clones/moodle-docker/',
                       stdout=stdout,
                       stderr=None,
                       addtoenv={
                           'COMPOSE_PROJECT_NAME': variant['projectname'],
                           'MOODLE_DOCKER_WWWROOT': M.get('path'),
                           **{k: v
                              for k, v in variant['env'].items() if v is not None}
                       })

    def _get_docker_metadata(self, identifier):
        filepath = self.Wp.getMetadataFile(identifier, 'docker.json')
        data = {'variants': []}
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
        except FileNotFoundError:
            pass
        return data

    def _get_docker_variant(self, identifier, label):
        data = self._get_docker_metadata(identifier)
        variant = next((v for v in data['variants'] if v.get('label') == label), None)
        if not variant:
            if not label:
                self.argumentError('The default variant does not exist.')
            self.argumentError('The variant {} does not exist.'.format(label))
        return variant

    def _has_containers(self, M, variant):
        resp = self._execute_docker_compose(M, variant, ['ps', '-a', '--services'], stdout=subprocess.PIPE)
        if resp[0] != 0:
            raise Exception('Error while checking if containers exist.')
        return len(resp[1]) > 0

    def _is_running(self, M, variant):
        resp = self._execute_docker_compose(M, variant, ['top'], stdout=subprocess.PIPE)
        if resp[0] != 0:
            raise Exception('Error while checking if containers are running.')
        return len(resp[1]) > 0

    def _save_docker_metadata(self, identifier, data):
        filepath = self.Wp.getMetadataFile(identifier, 'docker.json')
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return data