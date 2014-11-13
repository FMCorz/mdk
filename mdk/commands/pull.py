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
from .. import tools, jira, fetch
from ..command import Command
from ..tools import question


class PullCommand(Command):

    _arguments = [
        (
            ['-i', '--integration'],
            {
                'action': 'store_true',
                'help': 'checkout the stable branch before proceeding to the pull. Short for --mode integration.'
            }
        ),
        (
            ['-n', '--no-merge'],
            {
                'action': 'store_true',
                'dest': 'nomerge',
                'help': 'checkout the remote branch without merging. Short for --mode checkout.'
            }
        ),
        (
            ['--fetch-only'],
            {
                'action': 'store_true',
                'dest': 'fetchonly',
                'help': 'only fetches the remote branch, you can then use FETCH_HEAD. Short for --mode fetch.'
            }
        ),
        (
            ['-t', '--testing'],
            {
                'action': 'store_true',
                'help': 'checkout a testing branch before proceeding to the pull. Short for --mode testing.'
            }
        ),
        (
            ['-m', '--mode'],
            {
                'action': 'store',
                'choices': ['checkout', 'fetch', 'integration', 'pull', 'testing'],
                'default': 'pull',
                'help': 'define the mode to use'
            }
        ),
        (
            ['-p', '--prompt'],
            {
                'action': 'store_true',
                'help': 'prompts the user to choose the patch to download.'
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

        # Get the mode.
        mode = args.mode
        if args.fetchonly:
            mode = 'fetch'
        elif args.nomerge:
            mode = 'checkout'
        elif args.testing:
            mode = 'testing'
        elif args.integration:
            mode = 'integration'

        # Prompt?
        prompt = args.prompt

        # Tracker issue number.
        issuenb = args.issue
        if not issuenb:
            parsedbranch = tools.parseBranch(M.currentBranch())
            if not parsedbranch:
                raise Exception('Could not extract issue number from %s' % M.currentBranch())
            issuenb = parsedbranch['issue']

        issue = re.sub(r'(MDL|mdl)(-|_)?', '', issuenb)
        mdl = 'MDL-' + issue

        # Reading the information about the current instance.
        branch = M.get('branch')

        # Get information from Tracker
        logging.info('Retrieving information about %s from Moodle Tracker' % (mdl))
        fetcher = fetch.FetchTracker(M)

        try:
            if not prompt:
                fetcher.setFromTracker(mdl, branch)
        except (fetch.FetchTrackerRepoException, fetch.FetchTrackerBranchException) as e:
            prompt = True

        if prompt:
            patches = self.pickPatches(mdl)
            if not patches:
                raise Exception('Could not find any relevant information for a successful pull')
            fetcher.usePatches(patches)

        if mode == 'pull':
            fetcher.pull()
        elif mode == 'checkout':
            fetcher.checkout()
        elif mode == 'fetch':
            fetcher.fetch()
        elif mode == 'integration':
            fetcher.pull(into=M.get('stablebranch'))
        elif mode == 'testing':
            i = 0
            while True:
                i += 1
                suffix = 'test' if i <= 1 else 'test' + str(i)
                newBranch = M.generateBranchName(issue, suffix=suffix, version=branch)
                if not M.git().hasBranch(newBranch):
                    break
            fetcher.pull(into=newBranch, track=M.get('stablebranch'))

    def pickPatches(self, mdl):
        """Prompts the user to pick a patch"""

        J = jira.Jira()
        patches = J.getAttachments(mdl)
        patches = {k: v for k, v in patches.items() if v.get('filename').endswith('.patch')}
        toApply = []

        if len(patches) < 1:
            return False

        mapping = {}
        i = 1
        for key in sorted(patches.keys()):
            patch = patches[key]
            mapping[i] = patch
            print '{0:<2}: {1:<60} {2}'.format(i, key[:60], datetime.strftime(patch.get('date'), '%Y-%m-%d %H:%M'))
            i += 1

        while True:
            try:
                ids = question('What patches would you like to apply?')
                if ids.lower() == 'ankit':
                    logging.warning('Sorry, I am unable to punch a child at the moment...')
                    continue
                elif ids:
                    ids = re.split(r'\s*[, ]\s*', ids)
                    toApply = [mapping[int(i)] for i in ids if int(i) in mapping.keys()]
            except ValueError:
                logging.warning('Error while parsing the list of patches, try a little harder.')
                continue
            break

        return toApply

