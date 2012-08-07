#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import re
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description="Backports a branch")
parser.add_argument('-i', '--issues', metavar='issues', required=True, nargs='+', help='issues to be rebased')
parser.add_argument('-s', '--suffix', metavar='suffix', help='the suffix of the branch of those issues')
parser.add_argument('-v', '--versions', metavar='version', nargs='+', choices=[ str(x) for x in range(13, C('masterBranch')) ] + ['master'], help='versions to rebase the issues on. Ignored if name is set.')
parser.add_argument('-p', '--push', action='store_true', help='push the branch after successful rebase')
parser.add_argument('-r', '--remote', metavar='remote', help='the remote to push the branch to. Default is %s.' % C('mineRepo'))
parser.add_argument('-f', '--force-push', action='store_true', help='Force the push', dest='forcepush')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance to work on')
args = parser.parse_args()

instances = []
if args.versions == None:
	M = Wp.resolve(args.name)
	if not M:
	    debug('This is not a Moodle instance')
	    sys.exit(1)
	instances.append(M)
else:
	for v in args.versions:
		name = Wp.generateInstanceName(v)
		if Wp.isMoodle(name):
			instances.append(Wp.get(name))

# Loops over instances to rebase
for M in instances:
	debug('Working on %s' % (M.get('identifier')))
	M.git().fetch('origin')

	# Stash
	stash = M.git().stash(untracked=True)
	if stash[0] != 0:
		debug('Error while trying to stash your changes. Skipping %s.' % M.get('identifier'))
		debug(stash[2])
		continue
	elif not stash[1].startswith('No local changes'):
		debug('Stashed your local changes')

	# Looping over each issue to rebase
	for issue in args.issues:
		branch = M.generateBranchName(issue, suffix=args.suffix)
		if not M.git().hasBranch(branch):
			debug('Could not find branch %s' % (branch))
			continue

		# Rebase
		debug('> Rebasing %s...' % (branch))
		onto = 'origin/%s' % M.get('stablebranch')
		result = M.git().rebase(branch, onto=onto)
		if result[0] != 0:
			debug('Error while rebasing branch %s onto %s' % (branch, onto))
			debug(result[2])
			continue

		# Pushing branch
		if args.push:
			remote = args.remote
			if remote == None:
				remote = C('mineRepo')
			debug('Pushing %s to %s' % (branch, remote))
			result = M.git().push(remote=remote, branch=branch, force=args.forcepush)
			if result[0] != 0:
				debug('Error while pushing to remote')
				debug(result[2])
				continue

	# Stash pop
	if not stash[1].startswith('No local changes'):
		pop = M.git().stash(command='pop')
		if pop == False:
			debug('An error ocured while unstashing your changes')
		else:
			debug('Popped the stash')

	debug('')

debug('Done.')
