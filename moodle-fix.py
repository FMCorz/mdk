#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import re
import subprocess
import shlex

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

# Loading Moodle instance
M = None
if args.name != None:
	try:
		M = Wp.get(args.name)
	except:
		M = None
else:
	M = moodle.Moodle(os.getcwd())

if M == None or not M.isInstance(M.get('path')):
	debug('This is not a Moodle instance')
	sys.exit(1)

# Branch name
mdl = re.sub(r'MDL(-|_)?', '', args.issue, flags=re.I)
branch = C('wording.branchFormat') % (mdl, M.get('branch'))
if len(args.suffix) > 0:
	branch += C('wording.branchSuffixSeparator') + args.suffix

# Track
track = 'origin/%s' % M.get('stablebranch')

# Git repo
repo = git.Git(M.get('path'))

# Creating and checking out the new branch
if not repo.hasBranch(branch):
	if not repo.createBranch(branch, track):
		debug('Could not create branch %s' % branch)
		exit()
if not repo.checkout(branch):
	debug('Error while checkout out branch %s' % branch)
	exit()

debug('Branch %s checked out' % branch)


