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
parser.add_argument('-i', '--issue', metavar='issue', required=True, help='the issue to backport')
parser.add_argument('-s', '--suffix', metavar='suffix', help='the suffix of the branch of this issue')
parser.add_argument('-r', '--remote', metavar='remote', help='the remote to fetch from. Default is %s.' % C('mineRepo'))
parser.add_argument('-v', '--versions', metavar='version', required=True, nargs='+', choices=[ str(x) for x in range(13, C('masterBranch')) ] + ['master'], help='versions to backport to')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance to work on')
args = parser.parse_args()

M = Wp.resolve(args.name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

remote = args.remote
if remote == None:
	remote = C('mineRepo')


branch = M.generateBranchName(args.issue, suffix=args.suffix)
originaltrack = M.get('stablebranch')
if not M.git().hasBranch(branch):
	debug('Could not find original branch %s.' % (branch, remote))
	sys.exit(1)
if not M.git().hasBranch(branch):
	debug('Could not find original branch %s.' % (branch, remote))
	sys.exit(1)

# Begin backport
for v in args.versions:

	# Gets the instance to cherry-pick to
	name = Wp.generateInstanceName(v, integration=M.get('integration'))
	if not Wp.isMoodle(name):
		debug('Could not find instance %s for version %s' % (name, v))
		continue
	M2 = Wp.get(name)

	debug("Preparing cherry-pick of %s/%s in %s" % (remote, branch, name))

	# Fetch the remote to get reference to the branch to backport
	debug("Fetching remote %s..." % remote)
	M2.git().fetch(remote)

	# Creates a new branch if necessary
	newbranch = M2.generateBranchName(args.issue, suffix=args.suffix)
	track = 'origin/%s' % M2.get('stablebranch')
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

	# Picking the diff origin/MOODLE_23_STABLE..github/MDL-12345-master
	cherry = 'origin/%s..%s/%s' % (originaltrack, remote, branch)
	debug('Cherry-picking %s' % (cherry))
	result = M2.git().pick(cherry)
	if result[0] != 0:
		debug('Error while cherry-picking %s/%s in %s.' % (remote, branch, name))
		debug(result[2])
		continue

	debug('Instance %s successfully patched!' % name)
	debug('')

debug('Done.')
