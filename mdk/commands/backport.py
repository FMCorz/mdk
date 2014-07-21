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

import logging
from .. import tools, css, jira
from ..command import Command
from ..tools import yesOrNo


class BackportCommand(Command):

    _description = 'Backports a branch'

    def __init__(self, *args, **kwargs):
        super(BackportCommand, self).__init__(*args, **kwargs)
        self._arguments = [
            (
                ['-b', '--branch'],
                {
                    'help': 'the branch to backport if not the current one. If omitted, guessed from instance name.',
                    'metavar': 'branch'
                }
            ),
            (
                ['-f', '--force-push'],
                {
                    'action': 'store_true',
                    'dest': 'forcepush',
                    'help': 'force the push'
                }
            ),
            (
                ['-i', '--integration'],
                {
                    'action': 'store_true',
                    'help': 'backport to integration instances'
                }
            ),
            (
                ['-p', '--push'],
                {
                    'action': 'store_true',
                    'help': 'push the branch after successful backport'
                }
            ),
            (
                ['--push-to'],
                {
                    'dest': 'pushremote',
                    'help': 'the remote to push the branch to. Default is %s.' % self.C.get('myRemote'),
                    'metavar': 'remote'
                }
            ),
            (
                ['--patch'],
                {
                    'action': 'store_true',
                    'dest': 'patch',
                    'help': 'instead of pushing to a remote, this will upload a patch file to the tracker. Security issues use this by default if --push is set. This option discards most other flags.',
                }
            ),
            (
                ['-t', '--update-tracker'],
                {
                    'const': True,
                    'dest': 'updatetracker',
                    'help': 'to use with --push, also add the diff information to the tracker issue',
                    'metavar': 'gitref',
                    'nargs': '?'
                }
            ),
            (
                ['-v', '--versions'],
                {
                    'choices': [str(x) for x in range(13, int(self.C.get('masterBranch')))] + ['master'],
                    'help': 'versions to backport to',
                    'metavar': 'version',
                    'nargs': '+',
                    'required': True
                }
            ),
            (
                ['name'],
                {
                    'default': None,
                    'help': 'name of the instance to backport from. Can be omitted if branch is specified.',
                    'metavar': 'name',
                    'nargs': '?'
                }
            )
        ]

    def run(self, args):
        M = None
        branch = args.branch
        versions = args.versions
        integration = args.integration

        # If we don't have a branch, we need an instance
        M = self.Wp.resolve(args.name)
        if not M and not branch:
            raise Exception('This is not a Moodle instance')

        # Getting issue number
        if M and not branch:
            branch = M.currentBranch()

        # Parsing the branch
        parsedbranch = tools.parseBranch(branch)
        if not parsedbranch:
            raise Exception('Could not extract issue number from %s' % branch)
        issue = parsedbranch['issue']
        suffix = parsedbranch['suffix']
        version = parsedbranch['version']

        if args.push and not args.patch:
            mdlIssue = 'MDL-%s' % (issue)
            J = jira.Jira()
            args.patch = J.isSecurityIssue(mdlIssue)
            if args.patch:
                args.push = False
                logging.info('%s appears to be a security issue, switching to patch mode...' % (mdlIssue))

        # Original track
        originaltrack = tools.stableBranch(version)

        # Integration?
        if M:
            integration = M.isIntegration()

        def stashPop(stash):
            """Small helper to pop the stash has we have to do it in some different places"""
            if not stash[1].startswith('No local changes'):
                pop = M2.git().stash(command='pop')
                if pop[0] != 0:
                    logging.error('An error ocured while unstashing your changes')
                else:
                    logging.info('Popped the stash')

        # Begin backport
        for v in versions:

            # Gets the instance to cherry-pick to
            name = self.Wp.generateInstanceName(v, integration=integration)
            if not self.Wp.isMoodle(name):
                logging.warning('Could not find instance %s for version %s' % (name, v))
                continue
            M2 = self.Wp.get(name)

            logging.info("Preparing cherry-pick of %s/%s in %s" % (M.get('identifier'), branch, name))

            # Get hash list
            cherry = '%s/%s..%s' % (self.C.get('upstreamRemote'), originaltrack, branch)
            hashes = M.git().hashes(cherry)
            hashes.reverse()

            # Stash
            stash = M2.git().stash(untracked=False)
            if stash[0] != 0:
                logging.error('Error while trying to stash your changes. Skipping %s.' % M2.get('identifier'))
                logging.debug(stash[2])
                continue
            elif not stash[1].startswith('No local changes'):
                logging.info('Stashed your local changes')

            # Fetch the remote to get reference to the branch to backport
            logging.info("Fetching remote %s..." % (M.get('path')))
            M2.git().fetch(M.get('path'), branch)

            # Creates a new branch if necessary
            newbranch = M2.generateBranchName(issue, suffix=suffix)
            track = '%s/%s' % (self.C.get('upstreamRemote'), M2.get('stablebranch'))
            if not M2.git().hasBranch(newbranch):
                logging.info('Creating branch %s' % newbranch)
                if not M2.git().createBranch(newbranch, track=track):
                    logging.error('Could not create branch %s tracking %s in %s' % (newbranch, track, name))
                    stashPop(stash)
                    continue
                M2.git().checkout(newbranch)
            else:
                M2.git().checkout(newbranch)
                logging.info('Hard reset %s to %s' % (newbranch, track))
                M2.git().reset(to=track, hard=True)

            # Picking the diff upstream/MOODLE_23_STABLE..github/MDL-12345-master
            logging.info('Cherry-picking %s' % (cherry))
            result = M2.git().pick(hashes)
            if result[0] != 0:

                # Try to resolve the conflicts if any.
                resolveConflicts = True
                conflictsResolved = False
                while resolveConflicts:

                    # Check the list of possible conflicting files.
                    conflictingFiles = M2.git().conflictingFiles()
                    if conflictingFiles and len(conflictingFiles) == 1 and 'theme/bootstrapbase/style/moodle.css' in conflictingFiles:
                        logging.info('Conflicts found in bootstrapbase moodle CSS, trying to auto resolve...')
                        cssCompiler = css.Css(M2)
                        if cssCompiler.compile(theme='bootstrapbase', sheets=['moodle']):
                            M2.git().add('theme/bootstrapbase/style/moodle.css')
                            # We need to commit manually to prevent the editor to open.
                            M2.git().commit(filepath='.git/MERGE_MSG')
                            result = M2.git().pick(continu=True)
                            if result[0] == 0:
                                resolveConflicts = False
                                conflictsResolved = True
                    else:
                        resolveConflicts = False

                # We still have a dirty repository.
                if not conflictsResolved:
                    logging.error('Error while cherry-picking %s in %s.' % (cherry, name))
                    logging.debug(result[2])
                    if yesOrNo('The cherry-pick might still be in progress, would you like to abort it?'):
                        result = M2.git().pick(abort=True)
                        if result[0] > 0 and result[0] != 128:
                            logging.error('Could not abort the cherry-pick!')
                        else:
                            stashPop(stash)
                    logging.info('')
                    continue

            # Pushing branch
            if args.push:
                pushremote = args.pushremote
                if pushremote == None:
                    pushremote = self.C.get('myRemote')
                logging.info('Pushing %s to %s' % (newbranch, pushremote))
                result = M2.git().push(remote=pushremote, branch=newbranch, force=args.forcepush)
                if result[0] != 0:
                    logging.warning('Error while pushing to remote %s' % (pushremote))
                    logging.debug(result[2])
                    stashPop(stash)
                    continue

                # Update the tracker
                if args.updatetracker != None:
                    ref = None if args.updatetracker == True else args.updatetracker
                    M2.updateTrackerGitInfo(branch=newbranch, ref=ref)

            elif args.patch:
                if not M2.pushPatch(newbranch):
                    continue

            stashPop(stash)

            logging.info('Instance %s successfully patched!' % name)
            logging.info('')

        logging.info('Done.')
