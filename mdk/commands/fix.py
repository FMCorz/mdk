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
from ..tools import yesOrNo


class FixCommand(Command):

    _arguments = [
        (
            ['issue'],
            {
                'help': 'tracker issue or issue number'
            }
        ),
        (
            ['suffix'],
            {
                'default': '',
                'help': 'suffix of the branch',
                'nargs': '?'
            }
        ),
        (
            ['--autofix'],
            {
            'action': 'store_true',
                'default': '',
                'help': 'auto fix the bug related to the issue number'
            }
        ),
        (
            ['-n', '--name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name'
            }
        )
    ]
    _description = 'Creates a branch associated to an MDL issue'

    def run(self, args):

        # Loading instance
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        stablebranch = M.get('stablebranch')
        masterbranch = ''
        if stablebranch in ['master', 'main']:
            # Generate a branch name for master to check later whether there's already an existing working branch.
            masterbranch = M.generateBranchName(args.issue, args.suffix, 'master')

        # Branch name
        branch = M.generateBranchName(args.issue, suffix=args.suffix)

        # Track
        track = '%s/%s' % (self.C.get('upstreamRemote'), stablebranch)

        # Git repo
        repo = M.git()

        hasBranch = repo.hasBranch(branch)

        # In this case, `stablebranch` would be 'main'.
        if masterbranch != '' and not hasBranch:
            # If the *-main branch does not yet exist, check there's an already equivalent *-master branch.
            if repo.hasBranch(masterbranch):
                prompt = ('  It seems like you already have an existing working branch (%s).\n'
                          '  Would you like to check this out instead?')
                if yesOrNo(prompt % masterbranch):
                    # We'll check out the issue's *-master branch instead.
                    branch = masterbranch
                    hasBranch = True

        # Creating and checking out the new branch
        if not hasBranch:
            if not repo.createBranch(branch, track):
                raise Exception('Could not create branch %s' % branch)

        if not repo.checkout(branch):
            raise Exception('Error while checking out branch %s' % branch)

        logging.info('Branch %s checked out' % branch)

        # Auto-fixing the bug
        if args.autofix:
            logging.info('Auto fixing bug, please wait...')
            from time import sleep
            sleep(3)
            logging.info('That\'s a tricky one! Bear with me.')
            sleep(3)
            logging.info('Almost there!')
            sleep(3)
            logging.info('...')
            sleep(3)
            logging.info('You didn\'t think I was serious, did you?')
            sleep(3)
            logging.info('Now get to work!')
