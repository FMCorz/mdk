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
import shutil
from distutils.dir_util import copy_tree

from tools import debug, process
from config import Conf
import db
import git
import moodle

C = Conf()


class Workplace(object):

    def __init__(self, path = None, wwwDir = None, dataDir = None):
        if path == None:
            path = C.get('dirs.storage')
        if wwwDir == None:
            wwwDir = C.get('wwwDir')
        if dataDir == None:
            dataDir = C.get('dataDir')

        # Directory paths
        self.path = os.path.abspath(os.path.realpath(os.path.expanduser(path)))
        self.cache = os.path.abspath(os.path.realpath(os.path.expanduser(C.get('dirs.mdk'))))
        self.www = os.path.abspath(os.path.realpath(os.path.expanduser(C.get('dirs.www'))))

        if not os.path.isdir(self.path):
            raise Exception('Directory %s not found' % self.path)

        # Directory names
        self.wwwDir = wwwDir
        self.dataDir = dataDir

    def checkCachedClones(self, stable = True, integration = True):
        """Clone the official repository in a local cache"""
        cacheStable = os.path.join(self.cache, 'moodle.git')
        cacheIntegration = os.path.join(self.cache, 'integration.git')
        if not os.path.isdir(cacheStable) and stable:
            debug('Cloning stable repository into cache...')
            result = process('%s clone %s %s' % (C.get('git'), C.get('remotes.stable'), cacheStable))
            result = process('%s fetch -a' % C.get('git'), cacheStable)
        if not os.path.isdir(cacheIntegration) and integration:
            debug('Cloning integration repository into cache...')
            result = process('%s clone %s %s' % (C.get('git'), C.get('remotes.integration'), cacheIntegration))
            result = process('%s fetch -a' % C.get('git'), cacheIntegration)

    def create(self, name = None, version = 'master', integration = False, useCacheAsRemote = False):
        """Creates a new instance of Moodle"""
        if name == None:
            if integration:
                name = C.get('wording.prefixIntegration') + prefixVersion
            else:
                name = C.get('wording.prefixStable') + prefixVersion

        installDir = os.path.join(self.path, name)
        wwwDir = os.path.join(installDir, self.wwwDir)
        dataDir = os.path.join(installDir, self.dataDir)
        linkDir = os.path.join(self.www, name)

        if self.isMoodle(name):
            raise Exception('The Moodle instance %s already exists' % name)
        elif os.path.isdir(installDir):
            raise Exception('Installation path exists: %s' % installDir)

        self.checkCachedClones(not integration, integration)
        os.mkdir(installDir, 0755)
        os.mkdir(wwwDir, 0755)
        os.mkdir(dataDir, 0777)

        if integration:
            repository = os.path.join(self.cache, 'integration.git')
            upstreamRepository = C.get('remotes.integration')
        else:
            repository = os.path.join(self.cache, 'moodle.git')
            upstreamRepository = C.get('remotes.stable')

        # Clone the instances
        debug('Cloning repository...')
        if useCacheAsRemote:
            result = process('%s clone %s %s' % (C.get('git'), repository, wwwDir))
            upstreamRepository = repository
        else:
            copy_tree(repository, wwwDir)

        # Symbolic link
        if os.path.islink(linkDir):
            os.remove(linkDir)
        if os.path.isfile(linkDir) or os.path.isdir(linkDir): # No elif!
            debug('Could not create symbolic link')
            debug('Please manually create: ln -s %s %s' (wwwDir, linkDir))
        else:
            os.symlink(wwwDir, linkDir)

        # Symlink to dataDir in wwwDir
        if type(C.get('symlinkToData')) == str:
            linkDataDir = os.path.join(wwwDir, C.get('symlinkToData'))
            if not os.path.isfile(linkDataDir) and not os.path.isdir(linkDataDir) and not os.path.islink(linkDataDir):
                os.symlink(dataDir, linkDataDir)

        debug('Checking out branch...')
        repo = git.Git(wwwDir, C.get('git'))

        # Setting up the correct remote names
        repo.setRemote(C.get('myRemote'), C.get('remotes.mine'))
        repo.setRemote(C.get('upstreamRemote'), upstreamRepository)

        # Creating, fetch, pulling branches
        result = repo.fetch(C.get('upstreamRemote'))
        if version == 'master':
            repo.checkout('master')
        else:
            track = '%s/MOODLE_%s_STABLE' % (C.get('upstreamRemote'), version)
            branch = 'MOODLE_%s_STABLE' % version
            if not repo.hasBranch(branch) and not repo.createBranch(branch, track):
                debug('Could not create branch %s tracking %s' % (branch, track))
            else:
                repo.checkout(branch)
        repo.pull(remote = C.get('upstreamRemote'))

        M = self.get(name)
        return M

    def delete(self, name):
        """Completely remove an instance, database included"""

        # Instantiating the object also checks if it exists
        M = self.get(name)

        # Deleting the whole thing
        shutil.rmtree(os.path.join(self.path, name))

        # Deleting the possible symlink
        link = os.path.join(self.www, name)
        if os.path.islink(link):
            try:
                os.remove(link)
            except Exception as e:
                pass

        # Delete db
        DB = M.dbo()
        dbname = M.get('dbname')
        if DB and dbname and DB.dbexists(dbname):
            DB.dropdb(dbname)

    def generateInstanceName(self, version, integration=False, suffix=''):
        """Creates a name (identifier) from arguments"""

        # Wording version
        if version == 'master':
            prefixVersion = C.get('wording.prefixMaster')
        else:
            prefixVersion = version

        # Generating name
        if integration:
            name = C.get('wording.prefixIntegration') + prefixVersion
        else:
            name = C.get('wording.prefixStable') + prefixVersion

        # Append the suffix
        if suffix != None and suffix != '':
            name += C.get('wording.suffixSeparator') + suffix

        return name

    def get(self, name):
        """Returns an instance defined by its name, or by path"""
        # Extracts name from path
        if os.sep in name:
            path = os.path.abspath(os.path.realpath(name))
            if not path.startswith(self.path):
                raise Exception('Could not find Moodle instance at %s' % name)
            (head, name) = os.path.split(path)

        if not self.isMoodle(name):
            raise Exception('Could not find Moodle instance %s' % name)
        return moodle.Moodle(os.path.join(self.path, name, self.wwwDir), identifier = name)

    def getPath(self, name, mode = None):
        """Returns the path of an instance base on its name"""
        base = os.path.join(self.path, name)
        if mode == 'www':
            return os.path.join(base, self.wwwDir)
        elif mode == 'data':
            return os.path.join(base, self.dataDir)
        else:
            return base

    def isMoodle(self, name):
        """Checks whether a Moodle instance exist under this name"""
        d = os.path.join(self.path, name)
        if not os.path.isdir(d):
            return False

        wwwDir = os.path.join(d, self.wwwDir)
        dataDir = os.path.join(d, self.dataDir)
        if not os.path.isdir(wwwDir) or not os.path.isdir(dataDir):
            return False

        if not moodle.Moodle.isInstance(wwwDir):
            return False

        return True

    def list(self, integration = None, stable = None):
        """Return the list of Moodle instances"""
        dirs = os.listdir(self.path)
        names = []
        for d in dirs:
            if d == '.' or d == '..': continue
            if not os.path.isdir(os.path.join(self.path, d)): continue
            if not self.isMoodle(d): continue
            if integration != None or stable != None:
                M = self.get(d)
                if integration == False and M.isIntegration(): continue
                if stable == False and M.isStable(): continue
            names.append(d)
        return names

    def resolve(self, name = None, path = None):
        """Try to find a Moodle instance based on its name, a path or the working directory"""

        if name != None:
            if self.isMoodle(name):
                return self.get(name)
            return None

        if path == None:
            path = os.getcwd()
        path = os.path.realpath(os.path.abspath(path))

        # Is this path in a Moodle instance?
        if path.startswith(self.path):
            (head, tail) = os.path.split(path)
            while head.startswith(self.path):
                if self.isMoodle(tail):
                    return self.get(tail)
                (head, tail) = os.path.split(head)

        return False

    def resolveMultiple(self, names = []):
        """Return multiple instances"""
        if type(names) != list:
            if type(names) == str:
                names = list(names)
            else:
                raise Exception('Unexpected variable type')

        # Nothing has been passed, we use resolve()
        if len(names) < 1:
            M = self.resolve()
            if M:
                return [ M ]
            else:
                return [ ]

        # Try to resolve each instance
        result = []
        for name in names:
            M = self.resolve(name = name)
            if M:
                result.append(M)
            else:
                debug('Could not find instance called %s' % name)
        return result

    def updateCachedClones(self, integration = True, stable = True, verbose = True):
        """Update the cached clone of the repositories"""

        caches = []
        remote = 'origin'

        if integration:
            caches.append(os.path.join(self.cache, 'integration.git'))
        if stable:
            caches.append(os.path.join(self.cache, 'moodle.git'))

        for cache in caches:
            if not os.path.isdir(cache):
                continue

            repo = git.Git(cache, C.get('git'))

            verbose and debug('Working on %s...' % cache)
            verbose and debug('Fetching %s' % remote)
            if not repo.fetch(remote):
                raise Exception('Could not fetch %s in repository %s' % (remote, cache))

            remotebranches = repo.remoteBranches(remote)
            for hash, branch in remotebranches:
                verbose and debug('Updating branch %s' % branch)
                track = '%s/%s' % (remote, branch)
                if not repo.hasBranch(branch) and not repo.createBranch(branch, track = track):
                    raise Exception('Could not create branch %s tracking %s in repository %s' % (branch, track, cache))

                if not repo.checkout(branch):
                    raise Exception('Error while checking out branch %s in repository %s' % (branch, cache))

                if not repo.reset(to = track, hard = True):
                    raise Exception('Could not hard reset to %s in repository %s' % (branch, cache))

            verbose and debug('')

        return True
