#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2014 Frédéric Massart - FMCorz.net

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
from .. import tools, jira
from ..ci import CI, CIException
from ..command import Command


class PrecheckCommand(Command):

    _arguments = [
        (
            ['-b', '--branch'],
            {
                'metavar': 'branch',
                'help': 'the branch to pre-check. Defaults to the current branch.'
            }
        ),
        (
            ['-p', '--push'],
            {
                'action': 'store_true',
                'help': 'if set, the branch will be pushed to your default remote.'
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
    _description = 'Pre-checks a branch on the CI server'

    FAILED = -1

    def run(self, args):
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        against = M.get('stablebranch')
        branch = args.branch or M.currentBranch()
        if branch == 'HEAD':
            raise Exception('Cannot pre-check the HEAD branch')
        elif branch == against:
            raise Exception('Cannot pre-check the stable branch')

        parsedbranch = tools.parseBranch(branch)
        if not parsedbranch:
            raise Exception('Could not parse the branch')

        issue = parsedbranch['issue']

        if args.push:
            J = jira.Jira()
            if J.isSecurityIssue('MDL-%s' % (issue)):
                raise Exception('Security issues cannot be pre-checked')

            remote = self.C.get('myRemote')
            logging.info('Pushing branch \'%s\' to remote \'%s\'', branch, remote)
            result = M.git().push(remote, branch)
            if result[0] != 0:
                raise Exception('Could not push the branch:\n  %s' % result[2])

        ci = CI()
        try:
            # TODO Remove that ugly hack to get the read-only remote.
            logging.info('Invoking the build on the CI server...')
            build = ci.precheckRemoteBranch(self.C.get('repositoryUrl'), branch, against, 'MDL-%s' % issue)
        except CIException as e:
            raise e

        logging.info('Waiting for the build to complete, please wait...')
        build.block_until_complete(3)

        if build.is_good():
            logging.info('Precheck passed, good work!')
            sys.exit(0)
        else:
            logging.warning('Precheck failed, refer to:\n  %s', build.baseurl)
            sys.exit(self.FAILED)
