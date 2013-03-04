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
from lib.command import Command
from lib.tools import process


class PhpunitCommand(Command):

    _arguments = [
        (
            ['-f', '--force'],
            {
                'action': 'store_true',
                'help': 'force the initialisation'
            }
        ),
        (
            ['-r', '--run'],
            {
                'action': 'store_true',
                'help': 'also run the tests'
            }
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name',
                'nargs': '?'
            }
        )
    ]
    _description = 'Initialize PHPUnit'

    def run(self, args):

        # Loading instance
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        # Check if installed
        if not M.get('installed'):
            raise Exception('This instance needs to be installed first')

        # Run cli
        try:
            M.initPHPUnit(force=args.force)
            logging.info('PHPUnit ready!')
            if args.run:
                logging.info('Running PHPUnit')
                process('phpunit', M.path, None, None)
        except Exception as e:
            raise e
