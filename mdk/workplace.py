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
import logging
from .tools import mkdir, process, stableBranch
from .exceptions import CreateException
from .config import Conf
from . import git
from . import moodle

C = Conf()


class Workplace(object):

    """The name of the directory that contains the PHP files"""
    wwwDir = None

    """The name of the directory that contains Moodle data"""
    dataDir = None

    """The name of the directory that contains extra files"""
    extraDir = None

    """The name of the directory that makes extraDir web accessible, see getMdkWebDir"""
    mdkDir = None

    """The path to the storage directory"""
    path = None

    """The path to MDK cache"""
    cache = None

    """The path to the web accessible directory"""
    www = None

    def __init__(self, path=None, wwwDir=None, dataDir=None, extraDir=None, mdkDir=None):
        if path == None:
            path = C.get('dirs.storage')
        if wwwDir == None:
            wwwDir = C.get('wwwDir')
        if dataDir == None:
            dataDir = C.get('dataDir')
        if extraDir == None:
            extraDir = C.get('extraDir')
        if mdkDir == None:
            mdkDir = C.get('mdkDir')

        # Directory paths
        self.path = os.path.abspath(os.path.realpath(os.path.expanduser(path)))
        self.cache = os.path.abspath(os.path.realpath(os.path.expanduser(C.get('dirs.mdk'))))
        self.www = os.path.abspath(os.path.realpath(os.path.expanduser(C.get('dirs.www'))))

        if not os.path.isdir(self.path):
            raise Exception('Directory %s not found' % self.path)

        # Directory names
        self.wwwDir = wwwDir
        self.dataDir = dataDir
        self.extraDir = extraDir
        self.mdkDir = mdkDir

    def checkCachedClones(self, stable=True, integration=True):
        """Clone the official repository in a local cache"""
        cacheStable = self.getCachedRemote(False)
        cacheIntegration = self.getCachedRemote(True)

        if not os.path.isdir(cacheStable) and stable:
            logging.info('Cloning stable repository into cache...')

            # For faster clone, we will copy the integration clone if it exists.
            if os.path.isdir(cacheIntegration):
                shutil.copytree(cacheIntegration, cacheStable)
                repo = git.Git(cacheStable, C.get('git'))
                repo.setRemote('origin', C.get('remotes.stable'))
                # The repository is not updated at this stage, it has to be done manually.
            else:
                logging.info('This is going to take a while...')
                process('%s clone --mirror %s %s' % (C.get('git'), C.get('remotes.stable'), cacheStable))

        if not os.path.isdir(cacheIntegration) and integration:
            logging.info('Cloning integration repository into cache...')

            # For faster clone, we will copy the integration clone if it exists.
            if os.path.isdir(cacheStable):
                shutil.copytree(cacheStable, cacheIntegration)
                repo = git.Git(cacheIntegration, C.get('git'))
                repo.setRemote('origin', C.get('remotes.integration'))
                # The repository is not updated at this stage, it has to be done manually.
            else:
                logging.info('Have a break, this operation is slow...')
                process('%s clone --mirror %s %s' % (C.get('git'), C.get('remotes.integration'), cacheIntegration))

    def create(self, name=None, version='master', integration=False, useCacheAsRemote=False):
        """Creates a new instance of Moodle.
        The parameter useCacheAsRemote has been deprecated.
        """
        if name == None:
            name = self.generateInstanceName(version, integration=integration)

        if name == self.mdkDir:
            raise Exception('A Moodle instance cannot be called \'%s\', this is a reserved word.' % self.mdkDir)

        installDir = self.getPath(name)
        wwwDir = self.getPath(name, 'www')
        dataDir = self.getPath(name, 'data')
        extraDir = self.getPath(name, 'extra')
        linkDir = os.path.join(self.www, name)
        extraLinkDir = os.path.join(self.getMdkWebDir(), name)

        if self.isMoodle(name):
            raise CreateException('The Moodle instance %s already exists' % name)
        elif os.path.isdir(installDir):
            raise CreateException('Installation path exists: %s' % installDir)

        self.checkCachedClones(not integration, integration)
        self.updateCachedClones(stable=not integration, integration=integration, verbose=False)
        mkdir(installDir, 0755)
        mkdir(wwwDir, 0755)
        mkdir(dataDir, 0777)
        mkdir(extraDir, 0777)

        repository = self.getCachedRemote(integration)

        # Clone the instances
        logging.info('Cloning repository...')
        process('%s clone %s %s' % (C.get('git'), repository, wwwDir))

        # Symbolic link
        if os.path.islink(linkDir):
            os.remove(linkDir)
        if os.path.isfile(linkDir) or os.path.isdir(linkDir):  # No elif!
            logging.warning('Could not create symbolic link. Please manually create: ln -s %s %s' % (wwwDir, linkDir))
        else:
            os.symlink(wwwDir, linkDir)

        # Symlink to extra.
        if os.path.isfile(extraLinkDir) or os.path.isdir(extraLinkDir):
            logging.warning('Could not create symbolic link. Please manually create: ln -s %s %s' % (extraDir, extraLinkDir))
        else:
            os.symlink(extraDir, extraLinkDir)

        # Symlink to dataDir in wwwDir
        if type(C.get('symlinkToData')) == str:
            linkDataDir = os.path.join(wwwDir, C.get('symlinkToData'))
            if not os.path.isfile(linkDataDir) and not os.path.isdir(linkDataDir) and not os.path.islink(linkDataDir):
                os.symlink(dataDir, linkDataDir)

        logging.info('Checking out branch...')
        repo = git.Git(wwwDir, C.get('git'))

        # Removing the default remote origin coming from the clone
        repo.delRemote('origin')

        # Setting up the correct remote names
        repo.setRemote(C.get('myRemote'), C.get('remotes.mine'))
        repo.setRemote(C.get('upstreamRemote'), repository)

        # Creating, fetch, pulling branches
        repo.fetch(C.get('upstreamRemote'))
        branch = stableBranch(version)
        track = '%s/%s' % (C.get('upstreamRemote'), branch)
        if not repo.hasBranch(branch) and not repo.createBranch(branch, track):
            logging.error('Could not create branch %s tracking %s' % (branch, track))
        else:
            repo.checkout(branch)
        repo.pull(remote=C.get('upstreamRemote'))

        # Fixing up remote URLs if need be, this is done after pulling the cache one because we
        # do not want to contact the real origin server from here, it is slow and pointless.
        if not C.get('useCacheAsUpstreamRemote'):
            realupstream = C.get('remotes.integration') if integration else C.get('remotes.stable')
            if realupstream:
                repo.setRemote(C.get('upstreamRemote'), realupstream)

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
            except Exception:
                pass

        # Delete the extra dir symlink
        link = os.path.join(self.getMdkWebDir(), name)
        if os.path.islink(link):
            try:
                os.remove(link)
            except Exception:
                pass

        # Delete db
        DB = M.dbo()
        dbname = M.get('dbname')
        if DB and dbname and DB.dbexists(dbname):
            DB.dropdb(dbname)

    def generateInstanceName(self, version, integration=False, suffix='', identifier=None):
        """Creates a name (identifier) from arguments"""

        if identifier != None:
            # If an identifier is passed, we use it regardless of the other parameters.
            # Except for suffix.
            name = identifier.replace(' ', '_')
        else:
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
        return moodle.Moodle(os.path.join(self.path, name, self.wwwDir), identifier=name)

    def getCachedRemote(self, integration=False):
        """Return the path to the cached remote"""
        if integration:
            return os.path.join(self.cache, 'integration.git')
        else:
            return os.path.join(self.cache, 'moodle.git')

    def getExtraDir(self, name, subdir=None):
        """Return the path to the extra directory of an instance

        This also creates the directory if does not exist.
        """
        path = self.getPath(name, 'extra')
        if subdir:
            path = os.path.join(path, subdir)
        if not os.path.exists(path):
            mkdir(path, 0777)
        return path

    def getMdkWebDir(self):
        """Return (and create) the special MDK web directory."""
        mdkExtra = os.path.join(self.www, self.mdkDir)
        if not os.path.exists(mdkExtra):
            mkdir(mdkExtra, 0777)

        return mdkExtra

    def getPath(self, name, mode=None):
        """Returns the path of an instance base on its name"""
        base = os.path.join(self.path, name)
        if mode == 'www':
            return os.path.join(base, self.wwwDir)
        elif mode == 'data':
            return os.path.join(base, self.dataDir)
        elif mode == 'extra':
            return os.path.join(base, self.extraDir)
        else:
            return base

    def getUrl(self, name, extra=None):
        """Return the URL to an instance, or to its extra directory if extra is passed"""
        base = '%s://%s' % (C.get('scheme'), C.get('host'))

        if C.get('path') != '' and C.get('path') != None:
            base = '%s/%s' % (base, C.get('path'))

        wwwroot = None
        if not extra:
            wwwroot = '%s/%s' % (base, name)
        else:
            wwwroot = '%s/%s/%s/%s' % (base, self.mdkDir, name, extra)

        return wwwroot

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

    def list(self, integration=None, stable=None):
        """Return the list of Moodle instances"""
        dirs = os.listdir(self.path)
        names = []
        for d in dirs:
            if d == '.' or d == '..': continue
            if not os.path.isdir(os.path.join(self.path, d)): continue
            if not self.isMoodle(d): continue
            if integration != None or stable != None:
                M = self.get(d)
                if not integration and M.isIntegration(): continue
                if not stable and M.isStable(): continue
            names.append(d)
        return names

    def resolve(self, name=None, path=None):
        """Try to find a Moodle instance based on its name, a path or the working directory"""

        # A name was passed, is that a valid instance?
        if name != None:
            if self.isMoodle(name):
                return self.get(name)
            return None

        # If a path was not passed, let's use the current working directory.
        if path == None:
            path = os.getcwd()
        path = os.path.realpath(os.path.abspath(path))

        # Is this path in a Moodle instance?
        if path.startswith(self.path):

            # Get the relative path identifier/some/other/path
            relative = os.path.relpath(path, self.path)

            # Isolating the identifier, it should be the first directory
            (head, tail) = os.path.split(relative)
            while head:
                (head, tail) = os.path.split(head)

            if self.isMoodle(tail):
                return self.get(tail)

        return False

    def resolveMultiple(self, names=[]):
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
                return [M]
            else:
                return []

        # Try to resolve each instance
        result = []
        for name in names:
            M = self.resolve(name=name)
            if M:
                result.append(M)
            else:
                logging.info('Could not find instance called %s' % name)
        return result

    def updateCachedClones(self, integration=True, stable=True, verbose=True):
        """Update the cached clone of the repositories"""

        caches = []

        if integration:
            caches.append(os.path.join(self.cache, 'integration.git'))
        if stable:
            caches.append(os.path.join(self.cache, 'moodle.git'))

        for cache in caches:
            if not os.path.isdir(cache):
                continue

            repo = git.Git(cache, C.get('git'))

            if verbose:
                logging.info('Fetching cached repository %s...', os.path.basename(cache))
            else:
                logging.debug('Fetching cached repository %s...', os.path.basename(cache))
            if not repo.fetch():
                raise Exception('Could not fetch in repository %s' % (cache))

        return True
