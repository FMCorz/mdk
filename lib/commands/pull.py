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

import re
import os
import logging
from datetime import datetime
from lib import tools, jira
from lib.command import Command
from lib.tools import question


class PullCommand(Command):

    _arguments = [
        (
            ['-i', '--integration'],
            {
                'action': 'store_true',
                'help': 'checkout the stable branch before proceeding to the pull (Integration mode)'
            }
        ),
        (
            ['-n', '--no-merge'],
            {
                'action': 'store_true',
                'dest': 'nomerge',
                'help': 'checkout the remote branch without merging. Also this does not work with patch files. (No merge mode)'
            }
        ),
        (
            ['--fetch-only'],
            {
                'action': 'store_true',
                'dest': 'fetchonly',
                'help': 'only fetches the remote branch, you can then use FETCH_HEAD. Does not work with patch files. (Fetch mode)'
            }
        ),
        (
            ['-t', '--testing'],
            {
                'action': 'store_true',
                'help': 'checkout a testing branch before proceeding to the pull (Testing mode)'
            }
        ),
        (
            ['issue'],
            {
                'default': None,
                'help': 'tracker issue to pull from (MDL-12345, 12345). If not specified, read from current branch.',
                'metavar': 'issue',
                'nargs': '?'
            }
        )
    ]
    _description = 'Pull a branch from a tracker issue'

    def run(self, args):

        M = self.Wp.resolve()
        if not M:
            raise Exception('This is not a Moodle instance')

        if (args.testing and args.integration) or (args.testing and args.nomerge) or (args.integration and args.nomerge):
            raise Exception('You cannot combine --integration, --testing or --no-merge')

        # Tracker issue number.
        issuenb = args.issue
        if not issuenb:
            parsedbranch = tools.parseBranch(M.currentBranch(), self.C.get('wording.branchRegex'))
            if not parsedbranch:
                raise Exception('Could not extract issue number from %s' % M.currentBranch())
            issuenb = parsedbranch['issue']

        issue = re.sub(r'(MDL|mdl)(-|_)?', '', issuenb)
        mdl = 'MDL-' + issue

        # Reading the information about the current instance.
        branch = M.get('branch')

        # Get information from Tracker
        logging.info('Retrieving information about %s from Moodle Tracker' % (mdl))
        J = jira.Jira()
        issueInfo = J.getIssue(mdl)

        mode = 'pull' if not args.fetchonly else 'fetchonly'
        remoteUrl = issueInfo.get('named').get(self.C.get('tracker.fieldnames.repositoryurl'))
        remoteBranch = issueInfo.get('named').get(self.C.get('tracker.fieldnames.%s.branch' % (branch)))
        patchesToApply = []

        if (args.nomerge or args.fetchonly) and (not remoteUrl or not remoteBranch):
            # No merge and Fetch only require valid URL and branch
            mode = None

        elif (not args.nomerge and not args.fetchonly) and (not remoteUrl or not remoteBranch):
            # Attempting to find a patch
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
            raise Exception('Did not find enough information to pull a patch.')

        # Stash
        stash = None
        if mode != 'fetchonly':
            stash = M.git().stash(untracked=True)
            if stash[0] != 0:
                raise Exception('Error while trying to stash your changes. Exiting...')
            elif not stash[1].startswith('No local changes'):
                logging.info('Stashed your local changes')

        # Create a testing branch
        if args.testing:
            i = 0
            while True:
                i += 1
                suffix = 'test' if i <= 1 else 'test' + str(i)
                newBranch = M.generateBranchName(issue, suffix=suffix, version=branch)
                if not M.git().hasBranch(newBranch):
                    break
            track = '%s/%s' % (self.C.get('upstreamRemote'), M.get('stablebranch'))
            if not M.git().createBranch(newBranch, track=track):
                raise Exception('Could not create branch %s tracking %s' % (newBranch, track))
            if not M.git().checkout(newBranch):
                raise Exception('Could not checkout branch %s' % (newBranch))
            logging.info('Checked out branch %s' % (newBranch))

        # Checkout the stable branch
        elif args.integration:
            if not M.git().checkout(M.get('stablebranch')):
                logging.error('Could not checkout branch %s' % (M.get('stablebranch')))
            logging.info('Checked out branch %s' % (M.get('stablebranch')))

        # Create a no-merge branch
        elif args.nomerge:
            i = 0
            while True:
                i += 1
                suffix = 'nomerge' if i <= 1 else 'nomerge' + str(i)
                newBranch = M.generateBranchName(issue, suffix=suffix, version=branch)
                if not M.git().hasBranch(newBranch):
                    break
            track = '%s/%s' % (self.C.get('upstreamRemote'), M.get('stablebranch'))
            if not M.git().createBranch(newBranch, track=track):
                raise Exception('Could not create branch %s tracking %s' % (newBranch, track))
            if not M.git().checkout(newBranch):
                raise Exception('Could not checkout branch %s' % (newBranch))
            logging.info('Checked out branch %s' % (newBranch))
            mode = 'nomerge'

        # Let's pretend everything was fine at the start.
        result = True
        unstash = True

        if mode == 'pull':
            # Pull branch from tracker
            logging.info('Pulling branch %s from %s into %s' % (remoteBranch, remoteUrl, M.currentBranch()))
            result = M.git().pull(remote=remoteUrl, ref=remoteBranch)
            if result[0] != 0:
                logging.warning('Merge failed, please solve the conflicts and commit')
                result = False
                unstash = False

        elif mode == 'fetchonly':
            # Only fetches the branch from the remote
            logging.info('Fetching branch %s from %s' % (remoteBranch, remoteUrl))
            fetch = M.git().fetch(remote=remoteUrl, ref=remoteBranch)
            if fetch[0] != 0:
                logging.warning('Failed to fetch the remote branch')
            else:
                logging.info('Fetch successful, you can now use FETCH_HEAD')

        elif mode == 'patch':
            # Apply a patch from tracker
            files = []
            for patch in patchesToApply:
                dest = patch['mdk-filename']
                logging.info('Downloading %s' % (patch['filename']))
                if not J.download(patch['content'], dest):
                    logging.error('Failed to download. Aborting...')
                    result = False
                    files = []
                    break
                files.append(dest)

            if len(files) > 0:
                logging.info('Applying patch(es)...')
                if not M.git().apply(files):
                    logging.warning('Could not apply the patch(es), please apply manually')
                    result = False
                else:
                    for f in files:
                        os.remove(f)

        elif mode == 'nomerge':
            # Checking out the patch without merging it.
            logging.info('Fetching %s %s' % (remoteUrl, remoteBranch))
            M.git().fetch(remote=remoteUrl, ref=remoteBranch)
            logging.info('Hard reset to FETCH_HEAD')
            M.git().reset('FETCH_HEAD', hard=True)

        # Stash pop
        if unstash and stash and not stash[1].startswith('No local changes'):
            pop = M.git().stash(command='pop')
            if pop[0] != 0:
                logging.error('An error ocured while unstashing your changes')
            else:
                logging.info('Popped the stash')
        elif not unstash and stash:
            logging.warning('Note that some files have been left in your stash')

        if result:
            logging.info('Done.')

        # TODO Tidy up the messy logic above!
        # TODO Really, this needs some good tidy up!
        # TODO I'm being serious... this needs to crazy clean up!!
