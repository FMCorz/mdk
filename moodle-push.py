#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description="Push a branch to a remote.")
parser.add_argument('-b', '--branch', metavar='branch', help='the branch to push. Default is current branch.')
parser.add_argument('-r', '--remote', metavar='remote', help='remote to push to. Default is your remote.')
parser.add_argument('-s', '--include-stable', action='store_true', help='also push the stable branch (MOODLE_xx_STABLE, master)', dest='includestable')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance to work on')
args = parser.parse_args()

M = Wp.resolve(args.name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

# Setting remote
if args.remote == None:
	remote = 'mine'
else:
	remote = args.remote

# Setting branch
if args.branch == None:
	branch = M.branch()
	if branch == 'HEAD':
		debug('Cannot push HEAD branch')
		sys.exit(1)
else:
	branch = args.branch

# Pushing current branch
debug('Pushing branch %s to remote %s...' % (branch, remote))
result = M.git().push(remote, branch)
if result[0] != 0:
	debug(result[2])
	sys.exit(1)

# Pushing stable branch
if args.includestable:
	branch = M.get('stablebranch')
	debug('Pushing branch %s to remote %s...' % (branch, remote))
	result = M.git().push('mine', branch)
	if result[0] != 0:
		debug(result[2])
		sys.exit(1)

debug('Done.')
