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
import re
from lib import workplace, moodle, tools
from lib.tools import debug
from lib.config import C

Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description="Backports a branch")
parser.add_argument('-b', '--branch', metavar='branch', help='the branch to backport if not the current one. If omitted, guessed from instance name.')
parser.add_argument('-r', '--remote', metavar='remote', help='the remote to fetch from. Default is %s.' % C.get('myRemote'))
parser.add_argument('-i', '--integration', action='store_true', help='backport to integration instances.', dest='integration')
parser.add_argument('-d', '--dont-push', action='store_true', help='if name is specified, the branch is pushed to the remote (-p) before backporting. This disables this behaviour.', dest='dontpush')
parser.add_argument('-p', '--push', action='store_true', help='push the branch after successful backport')
parser.add_argument('-t', '--push-to', metavar='remote', help='the remote to push the branch to. Default is %s.' % C.get('myRemote'), dest='pushremote')
parser.add_argument('-f', '--force-push', action='store_true', help='Force the push', dest='forcepush')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance to backport from. Can be omitted if branch is specified.')
parser.add_argument('-v', '--versions', metavar='version', required=True, nargs='+', choices=[ str(x) for x in range(13, int(C.get('masterBranch'))) ] + ['master'], help='versions to backport to')
args = parser.parse_args()

M = None
branch = args.branch
versions = args.versions
remote = args.remote
integration = args.integration
if remote == None:
	remote = C.get('myRemote')

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

# Pushes the branch to the remote first
if M and not args.dontpush:
	debug('Pushing %s to %s' % (branch, remote))
	if not M.git().push(remote, branch):
		debug('Could not push %s to %s' % (branch, remote))
		sys.exit(1)

# Integration?
if M:
	integration = M.isIntegration()

# Begin backport
for v in versions:

	# Gets the instance to cherry-pick to
	name = Wp.generateInstanceName(v, integration=integration)
	if not Wp.isMoodle(name):
		debug('Could not find instance %s for version %s' % (name, v))
		continue
	M2 = Wp.get(name)

	debug("Preparing cherry-pick of %s/%s in %s" % (remote, branch, name))

	# Stash
	stash = M2.git().stash(untracked=True)
	if stash[0] != 0:
		debug('Error while trying to stash your changes. Skipping %s.' % M2.get('identifier'))
		debug(stash[2])
		continue
	elif not stash[1].startswith('No local changes'):
		debug('Stashed your local changes')

	# Fetch the remote to get reference to the branch to backport
	debug("Fetching remote %s..." % remote)
	M2.git().fetch(remote)

	# Creates a new branch if necessary
	newbranch = M2.generateBranchName(issue, suffix=suffix)
	track = '%s/%s' % (C.get('upstreamRemote'), M2.get('stablebranch'))
	if not M2.git().hasBranch(newbranch):
		debug('Creating branch %s' % newbranch)
		if not M2.git().createBranch(newbranch, track=track):
			debug('Could not create branch %s tracking %s in %s' % (newbranch, track, name))
			continue
		M2.git().checkout(newbranch)
	else:
		M2.git().checkout(newbranch)
		debug('Hard reset to %s' % (track))
		M2.git().reset(to=track, hard=True)

	# Picking the diff upstream/MOODLE_23_STABLE..github/MDL-12345-master
	cherry = '%s/%s..%s/%s' % (C.get('upstreamRemote'), originaltrack, remote, branch)
	debug('Cherry-picking %s' % (cherry))
	result = M2.git().pick(cherry)
	if result[0] != 0:
		debug('Error while cherry-picking %s/%s in %s.' % (remote, branch, name))
		debug(result[2])
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
			continue

	# Stash pop
	if not stash[1].startswith('No local changes'):
		pop = M2.git().stash(command='pop')
		if pop[0] != 0:
			debug('An error ocured while unstashing your changes')
		else:
			debug('Popped the stash')

	debug('Instance %s successfully patched!' % name)
	debug('')

debug('Done.')
