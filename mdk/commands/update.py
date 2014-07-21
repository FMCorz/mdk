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
import logging
from ..command import Command
from ..exceptions import UpgradeNotAllowed


class UpdateCommand(Command):

    _arguments = [
        (
            ['-a', '--all'],
            {
                'action': 'store_true',
                'dest': 'all',
                'help': 'update each instance'
            }
        ),
        (
            ['-c', '--cached'],
            {
                'action': 'store_true',
                'help': 'only update the cached (mirrored) repositories'
            }
        ),
        (
            ['-i', '--integration'],
            {
                'action': 'store_true',
                'dest': 'integration',
                'help': 'update integration instances'
            }
        ),
        (
            ['-s', '--stable'],
            {
                'action': 'store_true',
                'dest': 'stable',
                'help': 'update stable instances'
            }
        ),
        (
            ['-u', '--upgrade'],
            {
                'action': 'store_true',
                'dest': 'upgrade',
                'help': 'upgrade the instance after successful update'
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
    _description = 'Update the instance from remote'

    def run(self, args):

        if args.cached:
            self.updateCached()
            return

        # Updating instances
        names = args.names
        if args.all:
            names = self.Wp.list()
        elif args.integration or args.stable:
            names = self.Wp.list(integration=args.integration, stable=args.stable)

        Mlist = self.Wp.resolveMultiple(names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        self.updateCached()

        errors = []

        for M in Mlist:
            logging.info('Updating %s...' % M.get('identifier'))
            try:
                M.update()
            except Exception as e:
                errors.append(M)
                logging.warning('Error during the update of %s' % M.get('identifier'))
                logging.debug(e)
            else:
                if args.upgrade:
                    try:
                        M.upgrade()
                    except UpgradeNotAllowed as e:
                        logging.info('Skipping upgrade of %s (not allowed)' % (M.get('identifier')))
                        logging.debug(e)
                    except Exception as e:
                        errors.append(M)
                        logging.warning('Error during the upgrade of %s' % M.get('identifier'))
                        pass
            logging.info('')
        logging.info('Done.')

        if errors and len(Mlist) > 1:
            logging.info('')
            logging.warning('/!\ Some errors occurred on the following instances:')
            for M in errors:
                logging.warning('- %s' % M.get('identifier'))
            # Remove sys.exit and handle error code
            sys.exit(1)

    def updateCached(self):
        # Updating cache
        print 'Updating cached repositories'
        self.Wp.updateCachedClones(verbose=False)
