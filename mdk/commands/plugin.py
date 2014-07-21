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

from ..plugins import *
from ..command import Command


class PluginCommand(Command):

    _arguments = [
        (
            ['action'],
            {
                'metavar': 'action',
                'help': 'the action to perform',
                'sub-commands':
                    {
                        'download': (
                            {
                                'help': 'download a plugin in the instance'
                            },
                            [
                                (
                                    ['pluginname'],
                                    {
                                        'type': str,
                                        'metavar': 'pluginname',
                                        'default': None,
                                        'help': 'frankenstyle name of the plugin'
                                    }
                                ),
                                (
                                    ['name'],
                                    {
                                        'default': None,
                                        'help': 'name of the instance to work on',
                                        'metavar': 'name',
                                        'nargs': '?'
                                    }
                                ),
                                (
                                    ['-s', '--strict'],
                                    {
                                        'action': 'store_true',
                                        'help': 'prevent the download of a parent version if a file is not found for this branch',
                                    }
                                ),
                                (
                                    ['-f', '--force'],
                                    {
                                        'action': 'store_true',
                                        'help': 'overrides the plugin directory if it already exists'
                                    }
                                ),
                                (
                                    ['-c', '--no-cache'],
                                    {
                                        'action': 'store_true',
                                        'dest': 'nocache',
                                        'help': 'ignore the cached files'
                                    }
                                )
                            ]
                        ),
                        'install': (
                            {
                                'help': 'download and install a plugin'
                            },
                            [
                                (
                                    ['pluginname'],
                                    {
                                        'type': str,
                                        'metavar': 'pluginname',
                                        'default': None,
                                        'help': 'frankenstyle name of the plugin'
                                    }
                                ),
                                (
                                    ['name'],
                                    {
                                        'default': None,
                                        'help': 'name of the instance to work on',
                                        'metavar': 'name',
                                        'nargs': '?'
                                    }
                                ),
                                (
                                    ['-s', '--strict'],
                                    {
                                        'action': 'store_true',
                                        'help': 'prevent the download of a parent version if a file is not found for this branch',
                                    }
                                ),
                                (
                                    ['-f', '--force'],
                                    {
                                        'action': 'store_true',
                                        'help': 'overrides the plugin directory if it already exists'
                                    }
                                ),
                                (
                                    ['-c', '--no-cache'],
                                    {
                                        'action': 'store_true',
                                        'dest': 'nocache',
                                        'help': 'ignore the cached files'
                                    }
                                )
                            ]
                        )
                    }
            }
        )
    ]
    _description = 'Manage your plugins'

    def run(self, args):

        if args.action == 'download':

            M = self.Wp.resolve(args.name)
            if not M:
                raise Exception('This is not a Moodle instance')

            self.download(M, args)

        elif args.action == 'install':

            M = self.Wp.resolve(args.name)
            if not M:
                raise Exception('This is not a Moodle instance')

            if self.download(M, args):
                logging.info('Upgrading Moodle to install the new plugin')
                M.upgrade()

    def download(self, M, args):

        po = PluginObject(args.pluginname)
        if not args.force and PluginManager.hasPlugin(po, M):
            logging.error('The plugin is already present, set --force to overwrite it.')
            return False

        branch = M.get('branch')
        if branch == 'master':
            branch = C.get('masterBranch')
        branch = int(branch)

        fi = po.getZip(branch, fileCache=not args.nocache)
        if not fi and not args.strict:
            fi = po.getZip(branch - 1, fileCache=not args.nocache)

        if not fi:
            logging.warning('Could not find a file for this plugin')
            return False

        PluginManager.extract(fi, po, M, override=args.force)
        return True
