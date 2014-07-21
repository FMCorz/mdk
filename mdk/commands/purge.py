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


class PurgeCommand(Command):

    _arguments = [
        (
            ['-a', '--all'],
            {
                'action': 'store_true',
                'dest': 'all',
                'help': 'purge the cache on each instance'
            }
        ),
        (
            ['-i', '--integration'],
            {
                'action': 'store_true',
                'dest': 'integration',
                'help': 'purge the cache on integration instances'
            }
        ),
        (
            ['-s', '--stable'],
            {
                'action': 'store_true',
                'dest': 'stable',
                'help': 'purge the cache on stable instances'
            }
        ),
        (
            ['-m', '--manual'],
            {
                'action': 'store_true',
                'dest': 'manual',
                'help': 'perform a manual deletion of some cache in dataroot before executing the CLI script'
            }
        ),
        (
            ['names'],
            {
                'default': None,
                'help': 'name of the instances',
                'metavar': 'names',
                'nargs': '*'
            }
        )
    ]
    _description = 'Purge the cache of an instance'

    def run(self, args):

        # Resolving instances
        names = args.names
        if args.all:
            names = self.Wp.list()
        elif args.integration or args.stable:
            names = self.Wp.list(integration=args.integration, stable=args.stable)

        # Doing stuff
        Mlist = self.Wp.resolveMultiple(names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        for M in Mlist:
            logging.info('Purging cache on %s' % (M.get('identifier')))

            try:
                M.purge(manual=args.manual)
            except Exception as e:
                logging.error('Could not purge cache: %s' % e)
            else:
                logging.debug('Cache purged!')

            logging.info('')

        logging.info('Done.')
