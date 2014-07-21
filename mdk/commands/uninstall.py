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

import logging
from ..command import Command


class UninstallCommand(Command):

    _description = 'Uninstall a Moodle instance'
    _arguments = [
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name',
                'nargs': '?'
            }
        ),
        (
            ['-y'],
            {
                'action': 'store_true',
                'dest': 'do',
                'help': 'do not ask for confirmation'
            }
        )
    ]

    def run(self, args):

        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')
        elif not M.isInstalled():
            logging.info('This instance is not installed')
            return

        if not args.do:
            confirm = raw_input('Are you sure? (Y/n) ')
            if confirm != 'Y':
                logging.info('Aborting...')
                return

        logging.info('Uninstalling %s...' % M.get('identifier'))
        M.uninstall()
        logging.info('Done.')
