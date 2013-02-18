#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2012 Frédéric Massart - FMCorz.net

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
import argparse
from lib import workplace, tools, jira
from lib.tools import debug
from lib.config import Conf

Wp = workplace.Workplace()
C = Conf()

# Arguments
parser = argparse.ArgumentParser(description="Push a branch to a remote.")
parser.add_argument('-b', '--branch', metavar='branch', help='the branch to push. Default is current branch.')
parser.add_argument('-r', '--remote', metavar='remote', help='remote to push to. Default is your remote.')
parser.add_argument('-f', '--force', action='store_true', help='force the push (does not apply on the stable branch).')
parser.add_argument('-t', '--update-tracker', action='store_true', help='also add the diff information to the tracker issue.', dest='updatetracker')
parser.add_argument('-s', '--include-stable', action='store_true', help='also push the stable branch (MOODLE_xx_STABLE, master)', dest='includestable')
parser.add_argument('-k', '--force-stable', action='store_true', help='force the push on the stable branch', dest='forcestable')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance to work on')
args = parser.parse_args()

M = Wp.resolve(args.name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

# Setting remote
if args.remote == None:
    remote = C.get('myRemote')
else:
    remote = args.remote

# Setting branch
if args.branch == None:
    branch = M.currentBranch()
    if branch == 'HEAD':
        debug('Cannot push HEAD branch')
        sys.exit(1)
else:
    branch = args.branch

# Pushing current branch
debug('Pushing branch %s to remote %s...' % (branch, remote))
result = M.git().push(remote, branch, force=args.force)
if result[0] != 0:
    debug(result[2])
    sys.exit(1)

if args.updatetracker:
    # Getting issue number
    # Parsing the branch
    parsedbranch = tools.parseBranch(branch, C.get('wording.branchRegex'))
    if not parsedbranch:
        debug('Could not extract issue number from %s' % branch)
        sys.exit(1)
    issue = 'MDL-%s' % (parsedbranch['issue'])

    version = parsedbranch['version']

    # Get the jira config
    repositoryurl = C.get('repositoryUrl')
    diffurltemplate = C.get('diffUrlTemplate')
    stablebranch = M.get('stablebranch')
    upstreamremote = C.get('upstreamRemote')
    # Get the hash of the last upstream commit
    ref = '%s/%s' % (upstreamremote, stablebranch)
    headcommit = M.git().hashes(ref=ref, limit=1)[0]

    J = jira.Jira()
    diffurl = diffurltemplate.replace('%branch%', branch).replace('%stablebranch%', stablebranch).replace('%headcommit%', headcommit)

    fieldrepositoryurl = C.get('tracker.fieldnames.repositoryurl')
    fieldbranch = C.get('tracker.fieldnames.%s.branch' % version)
    fielddiffurl = C.get('tracker.fieldnames.%s.diffurl' % version)

    if not (fieldrepositoryurl or fieldbranch or fielddiffurl):
        debug('Cannot set tracker fields for this version (%s) as the field names are not configured in the config file.', version)

    else:
        debug('Setting tracker fields: \n\t%s: %s \n\t%s: %s \n\t%s: %s\n' % (fieldrepositoryurl, repositoryurl,
                                                                           fieldbranch, branch,
                                                                           fielddiffurl, diffurl))
        J.setCustomFields(issue, {fieldrepositoryurl: repositoryurl,
                                     fieldbranch: branch,
                                     fielddiffurl: diffurl})

# Pushing stable branch
if args.includestable:
    branch = M.get('stablebranch')
    debug('Pushing branch %s to remote %s...' % (branch, remote))
    result = M.git().push(remote, branch, force=args.forcestable)
    if result[0] != 0:
        debug(result[2])
        sys.exit(1)

debug('Done.')
