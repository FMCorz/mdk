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


class RemoveCommand(Command):

    _arguments = [
        (
            ['name'],
            {
                'help': 'name of the instance'
            }
        ),
        (
            ['-y'],
            {
                'action': 'store_true',
                'dest': 'do',
                'help': 'do not ask for confirmation'
            }
        ),
        (
            ['-f'],
            {
                'action': 'store_true',
                'dest': 'force',
                'help': 'force and do not ask for confirmation'
            }
        )
    ]
    _description = 'Completely remove an instance'

    def run(self, args):

        try:
            M = self.Wp.get(args.name)
        except:
            raise Exception('This is not a Moodle instance')

        if not args.do and not args.force:
            confirm = raw_input('Are you sure? (Y/n) ')
            if confirm != 'Y':
                logging.info('Aborting...')
                return

        logging.info('Removing %s...' % args.name)
        try:
            self.Wp.delete(args.name)
        except OSError:
            raise Exception('Error while deleting the instance.\n' +
                'This is probably a permission issue.\n' +
                'Run: sudo chmod -R 0777 %s' % self.Wp.getPath(args.name))

        logging.info('Instance removed')
