#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2013 Frédéric Massart - FMCorz.net

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
import os
from datetime import datetime
from lib import workplace, tools, jira
from lib.tools import debug, question
from lib.config import Conf

Wp = workplace.Workplace()
C = Conf()

# Arguments
parser = argparse.ArgumentParser(description="Pull a branch from a tracker issue.")
parser.add_argument('-i', '--integration', action='store_true', help='checkout the stable branch before proceeding to the pull (Integration mode).')
parser.add_argument('-n', '--no-merge', action='store_true', help='checkout the remote branch without merging. Also this does not work with patch files. (No merge mode)', dest='nomerge')
parser.add_argument('-t', '--testing', action='store_true', help='checkout a testing branch before proceeding to the pull (Testing mode).')
parser.add_argument('issue', metavar='issue', default=None, nargs='?', help='tracker issue to pull from (MDL-12345, 12345). If not specified, read from current branch.')
args = parser.parse_args()

M = Wp.resolve()
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

if (args.testing and args.integration) or (args.testing and args.nomerge) or (args.integration and args.nomerge):
    debug('You cannot combine --integration, --testing or --no-merge')
    sys.exit(1)

# Tracker issue number.
issuenb = args.issue
if not issuenb:
    parsedbranch = tools.parseBranch(M.currentBranch(), C.get('wording.branchRegex'))
    if not parsedbranch:
        debug('Could not extract issue number from %s' % M.currentBranch())
        sys.exit(1)
    issuenb = parsedbranch['issue']

issue = re.sub(r'(MDL|mdl)(-|_)?', '', issuenb)
mdl = 'MDL-' + issue

# Reading the information about the current instance.
branch = M.get('branch')

# Get information from Tracker
debug('Retrieving information about %s from Moodle Tracker' % (mdl))
J = jira.Jira()
issueInfo = J.getIssue(mdl)

mode = 'pull'
remoteUrl = issueInfo.get('named').get(C.get('tracker.fieldnames.repositoryurl'))
remoteBranch = issueInfo.get('named').get(C.get('tracker.fieldnames.%s.branch' % (branch)))
patchesToApply = []

if not args.nomerge and (not remoteUrl or not remoteBranch):
    mode = None
    attachments = issueInfo.get('fields').get('attachment')
    patches = {}
    for attachment in attachments:
        if attachment['filename'].endswith('.patch'):
            patches[attachment['filename']] = attachment

    if len(patches) > 0:
        mapping = {}
        i = 1
        for key in sorted(patches.keys()):
            patch = patches[key]
            mapping[i] = patch
            date = jira.Jira.parseDate(patch['created'])
            print '{0:<2}: {1:<60} {2}'.format(i, patch['filename'][:60], datetime.strftime(date, '%Y-%m-%d %H:%M'))
            i += 1

        ids = question('What patches would you like to apply?')
        if ids:
            ids = re.split(r'\s*[, ]\s*', ids)
            for i in ids:
                i = int(i)
                if not i in mapping.keys():
                    continue
                j = 0
                while True:
                    mapping[i]['mdk-filename'] = mapping[i]['filename'] + (('.' + str(j)) if j > 0 else '')
                    j += 1
                    if not os.path.isfile(mapping[i]['mdk-filename']):
                        break
                patchesToApply.append(mapping[i])
            mode = 'patch'
    else:
        mode = False

if not mode:
    debug('Did not find enough information to pull a patch.')
    sys.exit()

# Stash
stash = M.git().stash(untracked=True)
if stash[0] != 0:
    debug('Error while trying to stash your changes. Exiting...')
    sys.exit(1)
elif not stash[1].startswith('No local changes'):
    debug('Stashed your local changes')

# Create a testing branch
if args.testing:
    i = 0
    while True:
        i += 1
        suffix = 'test' if i <= 1 else 'test' + str(i)
        newBranch = M.generateBranchName(issue, suffix=suffix, version=branch)
        if not M.git().hasBranch(newBranch):
            break
    track = '%s/%s' % (C.get('upstreamRemote'), M.get('stablebranch'))
    M.git().createBranch(newBranch, track=track)
    if not M.git().checkout(newBranch):
        debug('Could not checkout branch %s' % (newBranch))
        sys.exit(1)
    debug('Checked out branch %s' % (newBranch))

# Checkout the stable branch
elif args.integration:
    if not M.git().checkout(M.get('stablebranch')):
        debug('Could not checkout branch %s' % (M.get('stablebranch')))
    debug('Checked out branch %s' % (M.get('stablebranch')))

# Create a no-merge branch
elif args.nomerge:
    i = 0
    while True:
        i += 1
        suffix = 'nomerge' if i <= 1 else 'nomerge' + str(i)
        newBranch = M.generateBranchName(issue, suffix=suffix, version=branch)
        if not M.git().hasBranch(newBranch):
            break
    track = '%s/%s' % (C.get('upstreamRemote'), M.get('stablebranch'))
    M.git().createBranch(newBranch, track=track)
    if not M.git().checkout(newBranch):
        debug('Could not checkout branch %s' % (newBranch))
        sys.exit(1)
    debug('Checked out branch %s' % (newBranch))
    mode = 'nomerge'

if mode == 'pull':
    # Pull branch from tracker
    debug('Pulling branch %s from %s into %s' % (remoteBranch, remoteUrl, M.currentBranch()))
    M.git().pull(remote=remoteUrl, ref=remoteBranch)

elif mode == 'patch':
    # Apply a patch from tracker
    files = []
    for patch in patchesToApply:
        dest = patch['mdk-filename']
        debug('Downloading %s' % (patch['filename']))
        if not J.download(patch['content'], dest):
            debug('Failed to download. Aborting...')
            files = []
            break
        files.append(dest)

    if len(files) > 0:
        debug('Applying patch(es)...')
        if not M.git().apply(files):
            debug('Could not apply the patch(es), please apply manually')
        else:
            for f in files:
                os.remove(f)

elif mode == 'nomerge':
    # Checking out the patch without merging it.
    debug('Fetching %s %s' % (remoteUrl, remoteBranch))
    M.git().fetch(remote=remoteUrl, ref=remoteBranch)
    debug('Hard reset to FETCH_HEAD')
    M.git().reset('FETCH_HEAD', hard=True)

# Stash pop
if not stash[1].startswith('No local changes'):
    pop = M.git().stash(command='pop')
    if pop[0] != 0:
        debug('An error ocured while unstashing your changes')
    else:
        debug('Popped the stash')

debug('Done.')

# TODO Tidy up the messy logic above!
