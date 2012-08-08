#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import re

from lib import config, git, tools, moodle, workplace
from lib.tools import debug

C = config.Conf().get

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
track = 'origin/%s' % M.get('stablebranch')

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
