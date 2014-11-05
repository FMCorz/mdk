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


class RebaseCommand(Command):

    _description = 'Rebase branches'

    def __init__(self, *args, **kwargs):
        super(RebaseCommand, self).__init__(*args, **kwargs)
        self._arguments = [
            (
                ['-i', '--issues'],
                {
                    'help': 'issues to be rebased',
                    'metavar': 'issues',
                    'nargs': '+',
                    'required': True
                }
            ),
            (
                ['-s', '--suffix'],
                {
                    'help': 'the suffix of the branch of those issues',
                    'metavar': 'suffix'
                }
            ),
            (
                ['-v', '--versions'],
                {
                    'choices': [str(x) for x in range(13, int(self.C.get('masterBranch')))] + ['master'],
                    'help': 'versions to rebase the issues on. Ignored if names is set.',
                    'metavar': 'version',
                    'nargs': '+'
                }
            ),
            (
                ['-p', '--push'],
                {
                    'action': 'store_true',
                    'help': 'push the branch after successful rebase'
                }
            ),
            (
                ['-t', '--update-tracker'],
                {
                    'action': 'store_true',
                    'dest': 'updatetracker',
                    'help': 'to use with --push, also add the diff information to the tracker issue'
                }
            ),
            (
                ['-r', '--remote'],
                {
                    'default': self.C.get('myRemote'),
                    'help': 'the remote to push the branch to. Default is %s.' % self.C.get('myRemote'),
                    'metavar': 'remote'
                }
            ),
            (
                ['-f', '--force-push'],
                {
                    'action': 'store_true',
                    'dest': 'forcepush',
                    'help': 'Force the push'
                }
            ),
            (
                ['names'],
                {
                    'default': None,
                    'help': 'name of the instances to rebase',
                    'metavar': 'names',
                    'nargs': '*'
                }
            )
        ]

    def run(self, args):

        names = args.names
        issues = args.issues
        versions = args.versions

        # If we don't have a version, we need an instance
        if not names and not versions:
            raise Exception('This is not a Moodle instance')

        # We don't have any names but some versions are set
        if not names:
            names = []
            for v in versions:
                names.append(self.Wp.generateInstanceName(v))

        # Getting instances
        Mlist = self.Wp.resolveMultiple(names)

        # Updating cache remotes
        logging.info('Updating cached repositories')
        self.Wp.updateCachedClones(verbose=False)

        # Loops over instances to rebase
        for M in Mlist:
            logging.info('Working on %s' % (M.get('identifier')))
            M.git().fetch(self.C.get('upstreamRemote'))

            # Test if currently in a detached branch
            if M.git().currentBranch() == 'HEAD':
                result = M.git().checkout(M.get('stablebranch'))
                # If we can't checkout the stable branch, that is probably because we are in an unmerged situation
                if not result:
                    logging.warning('Error. The repository seem to be on a detached branch. Skipping.')
                    continue

            # Stash
            stash = M.git().stash(untracked=True)
            if stash[0] != 0:
                logging.error('Error while trying to stash your changes. Skipping %s.' % M.get('identifier'))
                logging.debug(stash[2])
                continue
            elif not stash[1].startswith('No local changes'):
                logging.info('Stashed your local changes')

            # Looping over each issue to rebase
            for issue in issues:
                branch = M.generateBranchName(issue, suffix=args.suffix)
                if not M.git().hasBranch(branch):
                    logging.warning('Could not find branch %s' % (branch))
                    continue

                # Rebase
                logging.info('> Rebasing %s...' % (branch))
                base = '%s/%s' % (self.C.get('upstreamRemote'), M.get('stablebranch'))
                result = M.git().rebase(branch=branch, base=base)
                if result[0] != 0:
                    logging.warning('Error while rebasing branch %s on top of %s' % (branch, base))
                    if result[0] == 1 and result[2].strip() == '':
                        logging.debug('There must be conflicts.')
                        logging.info('Aborting... Please rebase manually.')
                        M.git().rebase(abort=True)
                    else:
                        logging.debug(result[2])
                    continue

                # Pushing branch
                if args.push:
                    remote = args.remote
                    logging.info('Pushing %s to %s' % (branch, remote))
                    result = M.git().push(remote=remote, branch=branch, force=args.forcepush)
                    if result[0] != 0:
                        logging.warning('Error while pushing to remote')
                        logging.debug(result[2])
                        continue

                    # Update the tracker
                    if args.updatetracker:
                        M.updateTrackerGitInfo(branch=branch)

            # Stash pop
            if not stash[1].startswith('No local changes'):
                pop = M.git().stash(command='pop')
                if pop[0] != 0:
                    logging.error('An error ocured while unstashing your changes')
                    logging.debug(pop[2])
                else:
                    logging.info('Popped the stash')

            logging.info('')

        logging.info('Done.')
