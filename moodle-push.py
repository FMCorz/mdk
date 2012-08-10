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
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description="Push a branch to a remote.")
parser.add_argument('-b', '--branch', metavar='branch', help='the branch to push. Default is current branch.')
parser.add_argument('-r', '--remote', metavar='remote', help='remote to push to. Default is your remote.')
parser.add_argument('-f', '--force', action='store_true', help='force the push (does not apply on the stable branch)')
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
	remote = C('myRemote')
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

# Pushing stable branch
if args.includestable:
	branch = M.get('stablebranch')
	debug('Pushing branch %s to remote %s...' % (branch, remote))
	result = M.git().push(remote, branch, force=args.forcestable)
	if result[0] != 0:
		debug(result[2])
		sys.exit(1)

debug('Done.')
