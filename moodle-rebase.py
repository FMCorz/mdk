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
from lib.config import Conf

Wp = workplace.Workplace()
C = Conf()

# Arguments
parser = argparse.ArgumentParser(description="Rebases branches")
parser.add_argument('-i', '--issues', metavar='issues', required=True, nargs='+', help='issues to be rebased')
parser.add_argument('-s', '--suffix', metavar='suffix', help='the suffix of the branch of those issues')
parser.add_argument('-v', '--versions', metavar='version', nargs='+', choices=[ str(x) for x in range(13, int(C.get('masterBranch'))) ] + ['master'], help='versions to rebase the issues on. Ignored if names is set.')
parser.add_argument('-p', '--push', action='store_true', help='push the branch after successful rebase')
parser.add_argument('-r', '--remote', metavar='remote', help='the remote to push the branch to. Default is %s.' % C.get('myRemote'))
parser.add_argument('-f', '--force-push', action='store_true', help='Force the push', dest='forcepush')
parser.add_argument('names', metavar='names', default=None, nargs='*', help='name of the instances to rebase')
args = parser.parse_args()

names = args.names
issues = args.issues
versions = args.versions

# If we don't have a version, we need an instance
if not names and not versions:
    debug('This is not a Moodle instance')
    sys.exit(1)

# We don't have any names but some versions are set
if not names:
	names = []
	for v in versions:
		names.append(Wp.generateInstanceName(v))

# Getting instances
Mlist = Wp.resolveMultiple(names)

# Loops over instances to rebase
for M in Mlist:
	debug('Working on %s' % (M.get('identifier')))
	M.git().fetch(C.get('upstreamRemote'))

	# Test if currently in a detached branch
	if M.git().currentBranch() == 'HEAD':
		result = M.git().checkout(M.get('stablebranch'))
		# If we can't checkout the stable branch, that is probably because we are in an unmerged situation
		if not result:
			debug('Error. The repository seem to be on a detached branch. Skipping.')
			continue

	# Stash
	stash = M.git().stash(untracked=True)
	if stash[0] != 0:
		debug('Error while trying to stash your changes. Skipping %s.' % M.get('identifier'))
		debug(stash[2])
		continue
	elif not stash[1].startswith('No local changes'):
		debug('Stashed your local changes')

	# Looping over each issue to rebase
	for issue in issues:
		branch = M.generateBranchName(issue, suffix=args.suffix)
		if not M.git().hasBranch(branch):
			debug('Could not find branch %s' % (branch))
			continue

		# Rebase
		debug('> Rebasing %s...' % (branch))
		base = '%s/%s' % (C.get('upstreamRemote'), M.get('stablebranch'))
		result = M.git().rebase(branch=branch, base=base)
		if result[0] != 0:
			debug('Error while rebasing branch %s on top of %s' % (branch, base))
			if result[0] == 1 and result[2].strip() == '':
				debug('There must be conflicts.')
				debug('Aborting... Please rebase manually.')
				M.git().rebase(abort=True)
			else:
				debug(result[2])
			continue

		# Pushing branch
		if args.push:
			remote = args.remote
			if remote == None:
				remote = C.get('myRemote')
			debug('Pushing %s to %s' % (branch, remote))
			result = M.git().push(remote=remote, branch=branch, force=args.forcepush)
			if result[0] != 0:
				debug('Error while pushing to remote')
				debug(result[2])
				continue

	# Stash pop
	if not stash[1].startswith('No local changes'):
		pop = M.git().stash(command='pop')
		if pop[0] != 0:
			debug('An error ocured while unstashing your changes')
			debug(result[2])
		else:
			debug('Popped the stash')

	debug('')

debug('Done.')
