#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

from tools import debug, process
import config
import db
import moodle

C = config.Conf().get

class Workplace():

    def __init__(self, path = None, wwwDir = None, dataDir = None):
        if path == None:
            path = C('dirs.storage')
        if wwwDir == None:
            wwwDir = C('wwwDir')
        if dataDir == None:
            dataDir = C('dataDir')

        if not os.path.isdir(path):
            raise Exception('Directory %s not found' % path)

        # Directory paths
        self.path = os.path.abspath(os.path.realpath(path))
        self.cache = os.path.abspath(os.path.realpath(C('dirs.moodle')))
        self.www = os.path.abspath(os.path.realpath(C('dirs.www')))

        # Directory names
        self.wwwDir = wwwDir
        self.dataDir = dataDir

    def checkCachedClones(self, stable = True, integration = True):
        """Clone the official repository in a local cache"""
        cacheStable = os.path.join(self.cache, 'moodle.git')
        cacheIntegration = os.path.join(self.cache, 'integration.git')
        if not os.path.isdir(cacheStable) and stable:
            debug('Cloning stable repository into cache...')
            result = process('%s clone %s %s' % (C('git'), C('remotes.stable'), cacheStable))
            result = process('%s fetch -a' % C('git'), cacheStable)
        if not os.path.isdir(cacheIntegration) and integration:
            debug('Cloning integration repository into cache...')
            result = process('%s clone %s %s' % (C('git'), C('remotes.integration'), cacheIntegration))
            result = process('%s fetch -a' % C('git'), cacheIntegration)

    def create(self, name = None, version = 'master', integration = False, useCacheAsRemote = False):
        """Creates a new instance of Moodle"""
        if name == None:
            if integration:
                name = C('wording.prefixIntegration') + prefixVersion
            else:
                name = C('wording.prefixStable') + prefixVersion

        installDir = os.path.join(self.path, name)
        wwwDir = os.path.join(installDir, self.wwwDir)
        dataDir = os.path.join(installDir, self.dataDir)
        linkDir = os.path.join(self.www, name)

        if self.isMoodle(name):
            raise Exception('This Moodle instance %s already exists' % name)
        elif os.path.isdir(installDir):
            raise Exception('Installation path exists: %s' % installDir)

        self.checkCachedClones(not integration, integration)
        os.mkdir(installDir, 0755)
        os.mkdir(wwwDir, 0755)
        os.mkdir(dataDir, 0777)

        if integration:
            repository = os.path.join(self.cache, 'integration.git')
        else:
            repository = os.path.join(self.cache, 'moodle.git')

        # Clone the instances
        debug('Cloning repository...')
        if useCacheAsRemote:
            result = process('%s clone %s %s' % (C('git'), repository, wwwDir))
        else:
            shutil.copytree(repository, wwwDir)

        # Symbolic link
        if os.path.islink(linkDir):
            os.remove(linkDir)
        if os.path.isfile(linkDir) or os.path.isdir(linkDir): # No elif!
            debug('Could not create symbolic link')
            debug('Please manually create: ln -s %s %s' (wwwDir, linkDir))
        else:
            os.symlink(wwwDir, linkDir)

        # Creating, fetch, pulling branches
        debug('Checking out branch...')
        M = self.get(name)
        git = M.git()
        result = git.fetch('origin')
        if version == 'master':
            git.checkout('master')
        else:
            track = 'origin/MOODLE_%s_STABLE' % version
            branch = 'MOODLE_%s_STABLE' % version
            if not git.createBranch(branch, track):
                debug('Could not create branch %s tracking %s' % (branch, track))
            else:
                git.checkout(branch)
        git.pull()
        git.addRemote(C('mineRepo'), C('remotes.mine'))

        return M

    def delete(self, name):
        """Completely remove an instance, database included"""

        # Instantiating the object also checks if it exists
        M = self.get(name)

        # Deleting the whole thing
        shutil.rmtree(os.path.join(self.path, name))

        # Deleting the possible symlink
        link = os.path.join(C('dirs.www'), name)
        if os.path.islink(link) and os.path.isdir(link):
            try:
                os.remove(link)
            except:
                pass

        # Delete db
        DB = M.dbo()
        dbname = M.get('dbname')
        if DB and dbname:
            DB.dropdb(dbname)

    def generateInstanceName(self, version, integration=False, suffix=''):
        """Creates a name (identifier) from arguments"""

        # Wording version
        if version == 'master':
            prefixVersion = C('wording.prefixMaster')
        else:
            prefixVersion = version

        # Generating name
        if integration:
            name = C('wording.prefixIntegration') + prefixVersion
        else:
            name = C('wording.prefixStable') + prefixVersion

        # Append the suffix
        if suffix != None and suffix != '':
            name += C('wording.suffixSeparator') + suffix

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

    def list(self):
        """Return the list of Moodle instances"""
        dirs = os.listdir(self.path)
        names = []
        for d in dirs:
            if d == '.' or d == '..': continue
            if not os.path.isdir(os.path.join(self.path, d)): continue
            if not self.isMoodle(d): continue
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

        # This path points right to a Moodle instance
        if moodle.Moodle.isInstance(path):
            return moodle.Moodle(path)

        # Is this path in a Moodle instance?
        if path.startswith(self.path):
            (head, tail) = os.path.split(path)
            while head.startswith(self.path):
                if self.isMoodle(tail):
                    return self.get(tail)
                (head, tail) = os.path.split(head)

        return False

    def updateCachedClones(self, integration = True, stable = True):
        """Update the cached clone of the repositories"""
        pass
