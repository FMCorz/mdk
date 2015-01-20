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
from .. import tools, jira
from ..command import Command
from ..tools import getMDLFromCommitMessage


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
                ['-p', '--patch'],
                {
                    'action': 'store_true',
                    'help': 'instead of pushing to a remote, this will upload a patch file to the tracker. Security issues use this by default. This option discards most other flags.'
                }
            ),
            (
                ['-t', '--update-tracker'],
                {
                    'const': True,
                    'dest': 'updatetracker',
                    'help': 'also add the diff information to the tracker issue. If gitref is passed, it is used as a starting point for the diff URL.',
                    'metavar': 'gitref',
                    'nargs': '?'
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

        # Extra test to see if the commit message is correct. This prevents easy typos in branch or commit messages.
        parsedbranch = tools.parseBranch(branch)
        if parsedbranch or branch != M.get('stablebranch'):
            message = M.git().messages(count=1)[0]

            mdl = getMDLFromCommitMessage(message)

            if parsedbranch:
                branchmdl = 'MDL-%s' % (parsedbranch['issue'])
            else:
                branchmdl = branch

            if not mdl or mdl != branchmdl:
                if not mdl:
                    print 'The MDL number could not be found in the commit message.'
                    print 'Commit: %s' % (message)

                elif mdl != branchmdl:
                    print 'The MDL number in the last commit does not match the branch being pushed to.'
                    print 'Branch: \'%s\' vs. commit: \'%s\'' % (branchmdl, mdl)

                answer = tools.question('Are you sure you want to continue?', default='n')
                if answer.lower()[0] != 'y':
                    print 'Exiting...'
                    return

        J = jira.Jira()

        # If the mode is not set to patch yet, and we can identify the MDL number.
        if not args.patch and parsedbranch:
            mdlIssue = 'MDL-%s' % (parsedbranch['issue'])
            try:
                args.patch = J.isSecurityIssue(mdlIssue)
                if args.patch:
                    logging.info('%s appears to be a security issue, switching to patch mode...', mdlIssue)
            except jira.JiraIssueNotFoundException:
                # The issue was not found, do not perform
                logging.warn('Could not check if %s is a security issue', mdlIssue)

        if args.patch:
            if not M.pushPatch(branch):
                return

        else:
            # Pushing current branch
            logging.info('Pushing branch %s to remote %s...' % (branch, remote))
            result = M.git().push(remote, branch, force=args.force)
            if result[0] != 0:
                raise Exception(result[2])

            # Update the tracker
            if args.updatetracker != None:
                ref = None if args.updatetracker == True else args.updatetracker
                M.updateTrackerGitInfo(branch=branch, ref=ref)

            # Pushing stable branch
            if args.includestable:
                branch = M.get('stablebranch')
                logging.info('Pushing branch %s to remote %s...' % (branch, remote))
                result = M.git().push(remote, branch, force=args.forcestable)
                if result[0] != 0:
                    raise Exception(result[2])

        logging.info('Done.')
