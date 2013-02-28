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
from lib import workplace, tools
from lib.tools import debug, yesOrNo
from lib.config import Conf

Wp = workplace.Workplace()
C = Conf()

# Arguments
parser = argparse.ArgumentParser(description="Backports a branch")
parser.add_argument('-b', '--branch', metavar='branch', help='the branch to backport if not the current one. If omitted, guessed from instance name.')
parser.add_argument('-i', '--integration', action='store_true', help='backport to integration instances.', dest='integration')
parser.add_argument('-p', '--push', action='store_true', help='push the branch after successful backport')
parser.add_argument('-t', '--push-to', metavar='remote', help='the remote to push the branch to. Default is %s.' % C.get('myRemote'), dest='pushremote')
parser.add_argument('-f', '--force-push', action='store_true', help='Force the push', dest='forcepush')
parser.add_argument('-j', '--update-jira', action='store_true', help='also add the github links to the jira issue.', dest='updatejira')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance to backport from. Can be omitted if branch is specified.')
parser.add_argument('-v', '--versions', metavar='version', required=True, nargs='+', choices=[str(x) for x in range(13, int(C.get('masterBranch')))] + ['master'], help='versions to backport to')
args = parser.parse_args()

M = None
branch = args.branch
versions = args.versions
integration = args.integration

# If we don't have a branch, we need an instance
M = Wp.resolve(args.name)
if not M and not branch:
    debug('This is not a Moodle instance')
    sys.exit(1)

# Getting issue number
if M and not branch:
    branch = M.currentBranch()

# Parsing the branch
parsedbranch = tools.parseBranch(branch, C.get('wording.branchRegex'))
if not parsedbranch:
    debug('Could not extract issue number from %s' % branch)
    sys.exit(1)
issue = parsedbranch['issue']
suffix = parsedbranch['suffix']
version = parsedbranch['version']

# Original track
originaltrack = tools.stableBranch(version)

# Integration?
if M:
    integration = M.isIntegration()


def stashPop(stash):
    """Small helper to pop the stash has we have to do it in some different places"""
    if not stash[1].startswith('No local changes'):
        pop = M2.git().stash(command='pop')
        if pop[0] != 0:
            debug('An error ocured while unstashing your changes')
        else:
            debug('Popped the stash')

# Begin backport
for v in versions:

    # Gets the instance to cherry-pick to
    name = Wp.generateInstanceName(v, integration=integration)
    if not Wp.isMoodle(name):
        debug('Could not find instance %s for version %s' % (name, v))
        continue
    M2 = Wp.get(name)

    debug("Preparing cherry-pick of %s/%s in %s" % (M.get('identifier'), branch, name))

    # Get hash list
    cherry = '%s/%s..%s' % (C.get('upstreamRemote'), originaltrack, branch)
    hashes = M.git().hashes(cherry)
    hashes.reverse()

    # Stash
    stash = M2.git().stash(untracked=True)
    if stash[0] != 0:
        debug('Error while trying to stash your changes. Skipping %s.' % M2.get('identifier'))
        debug(stash[2])
        continue
    elif not stash[1].startswith('No local changes'):
        debug('Stashed your local changes')

    # Fetch the remote to get reference to the branch to backport
    debug("Fetching remote %s..." % (M.get('path')))
    M2.git().fetch(M.get('path'), branch)

    # Creates a new branch if necessary
    newbranch = M2.generateBranchName(issue, suffix=suffix)
    track = '%s/%s' % (C.get('upstreamRemote'), M2.get('stablebranch'))
    if not M2.git().hasBranch(newbranch):
        debug('Creating branch %s' % newbranch)
        if not M2.git().createBranch(newbranch, track=track):
            debug('Could not create branch %s tracking %s in %s' % (newbranch, track, name))
            stashPop(stash)
            continue
        M2.git().checkout(newbranch)
    else:
        M2.git().checkout(newbranch)
        debug('Hard reset %s to %s' % (newbranch, track))
        M2.git().reset(to=track, hard=True)

    # Picking the diff upstream/MOODLE_23_STABLE..github/MDL-12345-master
    debug('Cherry-picking %s' % (cherry))
    result = M2.git().pick(hashes)
    if result[0] != 0:
        debug('Error while cherry-picking %s in %s.' % (cherry, name))
        debug(result[2])
        debug('')
        if yesOrNo('The cherry-pick might still be in progress, would you like to abort it?'):
            result = M2.git().pick(abort=True)
            if result[0] > 0 and result[0] != 128:
                debug('Could not abort the cherry-pick!')
            else:
                stashPop(stash)
        continue

    # Pushing branch
    if args.push:
        pushremote = args.pushremote
        if pushremote == None:
            pushremote = C.get('myRemote')
        debug('Pushing %s to %s' % (newbranch, pushremote))
        result = M2.git().push(remote=pushremote, branch=newbranch, force=args.forcepush)
        if result[0] != 0:
            debug('Error while pushing to remote %s' % (pushremote))
            debug(result[2])
            stashPop(stash)
            continue

    stashPop(stash)

    debug('Instance %s successfully patched!' % name)
    debug('')

debug('Done.')
