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
from lib import tools, jira
from lib.command import Command


class PushCommand(Command):

    _description = 'Push a branch to a remote'

    def __init__(self, *args, **kwargs):
        super(PushCommand, self).__init__(*args, **kwargs)
        self._arguments = [
            (
                ['-b', '--branch'],
                {
                    'metavar': 'branch',
                    'help': 'the branch to push. Default is current branch.'
                }
            ),
            (
                ['-f', '--force'],
                {
                    'action': 'store_true',
                    'help': 'force the push (does not apply on the stable branch)'
                }
            ),
            (
                ['-r', '--remote'],
                {
                    'help': 'remote to push to. Default is your remote.',
                    'default': self.C.get('myRemote'),
                    'metavar': 'remote'
                }
            ),
            (
                ['-t', '--update-tracker'],
                {
                    'action': 'store_true',
                    'dest': 'updatetracker',
                    'help': 'also add the diff information to the tracker issue.'
                }
            ),
            (
                ['-s', '--include-stable'],
                {
                    'action': 'store_true',
                    'dest': 'includestable',
                    'help': 'also push the stable branch (MOODLE_xx_STABLE, master)'
                }
            ),
            (
                ['-k', '--force-stable'],
                {
                    'action': 'store_true',
                    'dest': 'forcestable',
                    'help': 'force the push on the stable branch'
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
            )
        ]

    def run(self, args):

        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        # Setting remote
        remote = args.remote

        # Setting branch
        if args.branch == None:
            branch = M.currentBranch()
            if branch == 'HEAD':
                raise Exception('Cannot push HEAD branch')
        else:
            branch = args.branch

        # Pushing current branch
        logging.info('Pushing branch %s to remote %s...' % (branch, remote))
        result = M.git().push(remote, branch, force=args.force)
        if result[0] != 0:
            raise Exception(result[2])

        if args.updatetracker:
            # Getting issue number
            # Parsing the branch
            parsedbranch = tools.parseBranch(branch, self.C.get('wording.branchRegex'))
            if not parsedbranch:
                raise Exception('Could not extract issue number from %s' % branch)
            issue = 'MDL-%s' % (parsedbranch['issue'])

            version = parsedbranch['version']

            # Get the jira config
            repositoryurl = self.C.get('repositoryUrl')
            diffurltemplate = self.C.get('diffUrlTemplate')
            stablebranch = M.get('stablebranch')
            upstreamremote = self.C.get('upstreamRemote')
            # Get the hash of the last upstream commit
            ref = '%s/%s' % (upstreamremote, stablebranch)
            headcommit = M.git().hashes(ref=ref, limit=1)[0]

            J = jira.Jira()
            diffurl = diffurltemplate.replace('%branch%', branch).replace('%stablebranch%', stablebranch).replace('%headcommit%', headcommit)

            fieldrepositoryurl = self.C.get('tracker.fieldnames.repositoryurl')
            fieldbranch = self.C.get('tracker.fieldnames.%s.branch' % version)
            fielddiffurl = self.C.get('tracker.fieldnames.%s.diffurl' % version)

            if not (fieldrepositoryurl or fieldbranch or fielddiffurl):
                logging.error('Cannot set tracker fields for this version (%s) as the field names are not configured in the config file.', version)

            else:
                logging.info('Setting tracker fields: \n\t%s: %s \n\t%s: %s \n\t%s: %s\n' % (fieldrepositoryurl, repositoryurl,
                                                                                   fieldbranch, branch,
                                                                                   fielddiffurl, diffurl))
                J.setCustomFields(issue, {fieldrepositoryurl: repositoryurl,
                                             fieldbranch: branch,
                                             fielddiffurl: diffurl})

        # Pushing stable branch
        if args.includestable:
            branch = M.get('stablebranch')
            logging.info('Pushing branch %s to remote %s...' % (branch, remote))
            result = M.git().push(remote, branch, force=args.forcestable)
            if result[0] != 0:
                raise Exception(result[2])

        logging.info('Done.')
