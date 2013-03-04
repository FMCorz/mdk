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
from lib.command import Command
from lib.tools import debug


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
            ['-c', '--update-cache'],
            {
                'action': 'store_true',
                'dest': 'updatecache',
                'help': 'update the cached remotes. Useful when useCacheAsRemote is enabled.'
            }
        ),
        (
            ['-p', '--proceed'],
            {
                'action': 'store_true',
                'dest': 'process',
                'help': 'do not exit the process after updating the cache'
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

        # Updating cache only
        if args.updatecache:
            debug('Updating cached remote')
            self.Wp.updateCachedClones()
            debug('Done.')
            if not args.process:
                return
            debug('')

        # Updating instances
        names = args.names
        if args.all:
            names = self.Wp.list()
        elif args.integration or args.stable:
            names = self.Wp.list(integration=args.integration, stable=args.stable)

        Mlist = self.Wp.resolveMultiple(names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        errors = []

        for M in Mlist:
            debug('Updating %s...' % M.get('identifier'))
            try:
                M.update()
            except Exception as e:
                errors.append(M)
                debug('Error during the update of %s' % M.get('identifier'))
                debug(e)
            else:
                if args.upgrade:
                    try:
                        M.upgrade()
                    except Exception as e:
                        errors.append(M)
                        debug('Error during the upgrade of %s' % M.get('identifier'))
                        pass
            debug('')
        debug('Done.')

        if errors and len(Mlist) > 1:
            debug('')
            debug('/!\ Some errors occurred on the following instances:')
            for M in errors:
                debug('- %s' % M.get('identifier'))
            # Remove sys.exit and handle error code
            sys.exit(1)
