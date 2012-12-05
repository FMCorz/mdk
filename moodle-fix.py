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

import os
import sys
import argparse
import re

from lib import git, tools, moodle, workplace
from lib.tools import debug
from lib.config import Conf

C = Conf()

# Arguments
parser = argparse.ArgumentParser(description='Creates a branch associated to an MDL issue')
parser.add_argument('issue', help='issue number')
parser.add_argument('suffix', nargs='?', default='', help='suffix of the branch')
parser.add_argument('-n', '--name', metavar='name', default=None, help='name of the instance')
args = parser.parse_args()

Wp = workplace.Workplace()

# Loading instance
M = Wp.resolve(args.name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

# Branch name
branch = M.generateBranchName(args.issue, suffix=args.suffix)

# Track
track = '%s/%s' % (C.get('upstreamRemote'), M.get('stablebranch'))

# Git repo
repo = M.git()

# Creating and checking out the new branch
if not repo.hasBranch(branch):
	if not repo.createBranch(branch, track):
		debug('Could not create branch %s' % branch)
		sys.exit(1)
if not repo.checkout(branch):
	debug('Error while checkout out branch %s' % branch)
	sys.exit(1)

debug('Branch %s checked out' % branch)
