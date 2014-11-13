#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2014 Frédéric Massart - FMCorz.net

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
import jira
import logging


class Fetch(object):
    """Holds the logic and processing to fetch a remote and following actions into an instance"""

    _M = None
    _ref = None
    _repo = None

    _canCreateBranch = True
    _hasstashed = False

    def __init__(self, M, repo=None, ref=None):
        self._M = M
        self._repo = repo
        self._ref = ref

    def checkout(self):
        """Fetch and checkout the fetched branch"""
        self.fetch()
        logging.info('Checking out branch as FETCH_HEAD')
        if not self.M.git().checkout('FETCH_HEAD'):
            raise FetchException('Could not checkout FETCH_HEAD')

    def fetch(self):
        """Perform the fetch"""
        if not self.repo:
            raise FetchException('The repository to fetch from is unknown')
        elif not self.ref:
            raise FetchException('The ref to fetch is unknown')

        git = self.M.git()
        logging.info('Fetching %s from %s' % (self.ref, self.repo))
        result = git.fetch(remote=self.repo, ref=self.ref)
        if not result:
            raise FetchException('Error while fetching %s from %s' % (self.ref, self.repo))

    def _merge(self):
        """Protected method to merge FETCH_HEAD into the current branch"""
        logging.info('Merging into current branch')
        if not self.M.git().merge('FETCH_HEAD'):
            raise FetchException('Merge failed, resolve the conflicts and commit')

    def pull(self, into=None, track=None):
        """Fetch and merge the fetched branch into a branch passed as param"""
        self._stash()

        try:
            self.fetch()
            git = self.M.git()

            if into:
                logging.info('Switching to branch %s' % (into))

                if not git.hasBranch(into):
                    if self.canCreateBranch:
                        if not git.createBranch(into, track=track):
                            raise FetchException('Could not create the branch %s' % (into))
                    else:
                        raise FetchException('Branch %s does not exist and create branch is forbidden' % (into))

                if not git.checkout(into):
                    raise FetchException('Could not checkout branch %s' % (into))

            self._merge()

        except FetchException as e:
            if self._hasstashed:
                logging.warning('An error occured. Some files may have been left in your stash.')
            raise e

        self._unstash()

    def setRef(self, ref):
        """Set the reference to fetch"""
        self._ref = ref

    def setRepo(self, repo):
        """Set the repository to fetch from"""
        self._repo = repo

    def _stash(self):
        """Protected method to stash"""
        stash = self.M.git().stash(untracked=True)
        if stash[0] != 0:
            raise FetchException('Error while trying to stash your changes')
        elif not stash[1].startswith('No local changes'):
            logging.info('Stashed your local changes')
            self._hasstashed = True

    def _unstash(self):
        """Protected method to unstash"""
        if self._hasstashed:
            pop = self.M.git().stash(command='pop')
            if pop[0] != 0:
                logging.error('An error ocured while unstashing your changes')
            else:
                logging.info('Popped the stash')
        self._hasstashed = False

    @property
    def canCreateBranch(self):
        return self._canCreateBranch

    @property
    def into(self):
        return self._into

    @property
    def M(self):
        return self._M

    @property
    def ref(self):
        return self._ref

    @property
    def repo(self):
        return self._repo


class FetchTracker(Fetch):
    """Pretty dodgy implementation of Fetch to work with the tracker.

        If a list of patches is set, we override the git methods to fetch from a remote
        to use the patches instead. I am not super convinced by this design, but at
        least the logic to fetch/pull/merge is more or less self contained.
    """

    _J = None
    _cache = None
    _patches = None

    def __init__(self, *args, **kwargs):
        super(FetchTracker, self).__init__(*args, **kwargs)
        self._J = jira.Jira()
        self._cache = {}

    def checkout(self):
        if not self.patches:
            return super(FetchTracker, self).checkout()

        self.fetch()

    def fetch(self):
        if not self.patches:
            return super(FetchTracker, self).fetch()

        for patch in self.patches:
            j = 0
            dest = None
            while True:
                downloadedTo = patch.get('filename') + (('.' + str(j)) if j > 0 else '')
                dest = os.path.join(self.M.get('path'), downloadedTo)
                j += 1
                if not os.path.isfile(dest):
                    patch['downloadedTo'] = downloadedTo
                    break
            
            logging.info('Downloading patch as %s' % (patch.get('downloadedTo')))
            if not dest or not self.J.download(patch.get('url'), dest):
                raise FetchTrackerException('Failed to download the patch to %s' % (dest))


    def _merge(self):
        if not self.patches:
            return super(FetchTracker, self)._merge()

        patchList = [patch.get('downloadedTo') for patch in self.patches]
        git = self.M.git()
        if not git.apply(patchList):
            raise FetchTrackerException('Could not apply the patch(es), please apply manually')
        else:
            for f in patchList:
                os.remove(f)
        logging.info('Patches applied successfully')

    def getPullInfo(self, mdl):
        """Return the pull information

            This implements its own local cache because we could potentially
            call it multiple times during the same request. This is bad though.
        """
        if not self._cache.has_key(mdl):
            issueInfo = self.J.getPullInfo(mdl)
            self._cache[mdl] = issueInfo
        return self._cache[mdl]

    def setFromTracker(self, mdl, branch):
        """Sets the repo and ref according to the tracker information"""
        issueInfo = self.getPullInfo(mdl)

        repo = issueInfo.get('repo', None)
        if not repo:
            raise FetchTrackerRepoException('Missing information about the repository to pull from on %s' % (mdl))

        ref = issueInfo.get('branches').get(str(branch), None)
        if not ref:
            raise FetchTrackerBranchException('Could not find branch info on %s' % (str(branch), mdl))

        self.setRepo(repo)
        self.setRef(ref.get('branch'))

    def usePatches(self, patches):
        """List of patches (returned by jira.Jira.getAttachments) to work with instead of the standard repo and ref"""
        self._patches = patches

    @property
    def J(self):
        return self._J

    @property
    def patches(self):
        return self._patches


class FetchException(Exception):
    pass


class FetchTrackerException(FetchException):
    pass


class FetchTrackerBranchException(FetchTrackerException):
    pass


class FetchTrackerRepoException(FetchTrackerException):
    pass