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

import http.client
import json
import logging
import os
from pathlib import Path
import shutil
import zipfile
from math import floor
from tempfile import gettempdir
from urllib.parse import urlencode
from urllib.request import urlretrieve

from . import tools
from .config import Conf
from .moodle import Moodle
from .paths import ComponentResolver

C = Conf()


def get_component_resolver(M: Moodle) -> ComponentResolver:
    dirroot = Path(M.path).resolve()
    admin = M.get('admin', 'admin') or 'admin'
    return ComponentResolver(dirroot, admin=admin)


class PluginManager(object):

    @classmethod
    def extract(cls, f, plugin, M, override=False):
        """Extract a plugin zip file to the plugin directory of M"""

        if type(plugin) != PluginObject:
            raise ValueError('PluginObject expected')

        if not override and cls.hasPlugin(plugin, M):
            raise Exception('Plugin directory already exists')

        if not cls.validateZipFile(f, plugin.name):
            raise Exception('Invalid zip file')

        resolver = get_component_resolver(M)
        extractIn = resolver.get_plugintype_directory(plugin.t)
        if not extractIn:
            raise Exception('Unable to resolve the plugin type directory')

        zp = zipfile.ZipFile(f)
        try:
            logging.info('Extracting plugin...')
            rootDir = os.path.commonprefix(zp.namelist())
            zp.extractall(extractIn)
            if plugin.name != rootDir.rstrip('/'):
                orig = extractIn / rootDir
                dest = extractIn / plugin.name

                # Merge directories
                for src_dir, dirs, files in os.walk(orig):
                    src_dir = Path(src_dir)
                    dst_dir = dest / src_dir.relative_to(orig)
                    if not dst_dir.exists():
                        dst_dir.mkdir()
                    for file_ in files:
                        src_file = src_dir / file_
                        dst_file = dst_dir / file_
                        if dst_file.exists():
                            dst_file.unlink()
                        src_file.rename(dst_file)

                shutil.rmtree(orig)

        except OSError:
            raise Exception('Error while extracting the files')

    @classmethod
    def getTypeAndName(cls, plugin):
        """Accepts a full plugin name 'mod_book' and returns the type and plugin name"""

        if plugin == 'moodle' or plugin == 'core' or plugin == '':
            return ('core', None)

        if not '_' in plugin:
            t = 'mod'
            name = plugin

        else:
            (t, name) = plugin.split('_', 1)
            if t == 'moodle':
                t = 'core'

        return (t, name)

    @classmethod
    def hasPlugin(cls, plugin, M):
        resolver = get_component_resolver(M)
        target = resolver.get_component_directory(plugin.component)
        return target is not None and target.exists()

    @classmethod
    def isPlugin(cls, plugin, M):
        """Whether the plugin is a valid plugin, and not a subsystem."""
        resolver = get_component_resolver(M)
        return resolver.get_plugintype_directory(plugin.t) is not None

    @classmethod
    def validateZipFile(cls, f, name):
        zp = zipfile.ZipFile(f, 'r')

        # Checking that the content is all contained in one single directory
        rootDir = os.path.commonprefix(zp.namelist())
        if rootDir == '':
            return False
        return True

    @classmethod
    def deleteDirectoryTree(cls, plugin: 'PluginObject', M):
        resolver = get_component_resolver(M)
        fullpath = resolver.get_component_directory(plugin.component)

        if not fullpath or fullpath.name != plugin.name:
            raise ValueError('Unexpeced component.')

        if fullpath.is_dir() and fullpath.exists():
            shutil.rmtree(fullpath)


class PluginObject(object):

    component: str
    t: str
    name: str

    def __init__(self, component):
        self.t, name = PluginManager.getTypeAndName(component)
        assert type(name) is str, 'Unexpected component'
        self.name = name
        self.component = f'{self.t}_{self.name}'
        self.dlinfo = {}

    def getDownloadInfo(self, branch):
        if not self.dlinfo.get(branch, False):
            self.dlinfo[branch] = PluginRepository().info(self.component, branch)
        return self.dlinfo.get(branch, False)

    def getZip(self, branch, fileCache=None):
        dlinfo = self.getDownloadInfo(branch)
        if not dlinfo:
            return False
        return dlinfo.download(fileCache)


class PluginDownloadInfo(dict):

    def download(self, fileCache=None, cacheDir=C.get('dirs.mdk')):
        """Download a plugin"""

        if fileCache == None:
            fileCache = C.get('plugins.fileCache')

        dest = os.path.abspath(os.path.expanduser(os.path.join(cacheDir, 'plugins')))
        if not fileCache:
            dest = gettempdir()

        if not 'version' in list(self.keys()):
            raise ValueError('Expecting the key version')
        elif not 'downloadurl' in list(self.keys()):
            raise ValueError('Expecting the key downloadurl')
        elif not 'component' in list(self.keys()):
            raise ValueError('Expecting the key component')
        elif not 'branch' in list(self.keys()):
            raise ValueError('Expecting the key branch')

        dl = self.get('downloadurl')
        plugin = self.get('component')
        branch = self.get('branch')
        target = os.path.join(dest, '%s-%d.zip' % (plugin, branch))
        md5sum = self.get('downloadmd5')
        release = self.get('release', 'Unknown')

        if fileCache:
            if not os.path.isdir(dest):
                logging.debug('Creating directory %s' % (dest))
                tools.mkdir(dest, 0o777)

            if os.path.isfile(target) and (md5sum == None or tools.md5file(target) == md5sum):
                logging.info('Found cached plugin file: %s' % (os.path.basename(target)))
                return target

        logging.info('Downloading %s (%s)' % (plugin, release))
        if logging.getLogger().level <= logging.INFO:
            urlretrieve(dl, target, tools.downloadProcessHook)
            # Force a new line after the hook display
            logging.info('')
        else:
            urlretrieve(dl, target)

        # Highly memory inefficient MD5 check
        if md5sum and tools.md5file(target) != md5sum:
            os.remove(target)
            logging.warning('Bad MD5 sum on downloaded file')
            return False

        return target


class PluginRepository(object):

    apiversion = '1.2'
    uri = '/api'
    host = 'download.moodle.org'
    ssl = True
    localRepository = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginRepository, cls).__new__(cls, *args, **kwargs)
            cls._instance.localRepository = C.get('plugins.localRepository')
            cls._instance.localRepository = {} if cls._instance.localRepository == None else cls._instance.localRepository
        return cls._instance

    def convert_branch(self, branch):
        """Converts the branch name to the correct version, e. g. 39 must become 3.9, but 311 must be
        3.11 instead of 31.1 and finally 402 must become 4.2 instead of 4.02"""
        if branch <= 39:
            return '{:.1f}'.format(float(branch) / 10.)
        else:
            major = floor(branch / 100.)
            minor = branch - major * 100
            if minor >= 10:
                return '{:.2f}'.format(float(branch) / 100.)
            return '{:.1f}'.format(major + minor / 10.)

    def info(self, plugin, branch):
        """Gets the download information of the plugin, branch is expected to be
        a whole integer, such as 25 for 2.5, etc...
        """

        if type(branch) != int:
            raise ValueError('Branch must be an integer')

        # Checking local repository
        lr = self.localRepository.get(plugin, False)
        if lr:
            info = lr.get(str(branch), None)
            if not info:
                versions = [v for v in range(branch, 18, -1)]
                for v in versions:
                    info = lr.get('>=%d' % v, None)
                    if info:
                        break
            if info and info.get('downloadurl'):
                logging.info('Found a compatible version for the plugin in local repository')
                info['component'] = plugin
                info['branch'] = branch
                info['version'] = branch
                return PluginDownloadInfo(info)

        # Contacting the remote repository
        data = {"branch": self.convert_branch(branch), "plugin": plugin}

        logging.info('Retrieving information for plugin %s and branch %s' % (data['plugin'], data['branch']))
        try:
            resp = self.request('pluginfo.php', 'GET', data)
        except PluginRepositoryNotFoundException:
            logging.info('No result found')
            return False
        except PluginRepositoryException:
            logging.warning('Error while retrieving information from the plugin database')
            return False

        pluginfo = resp.get('data', {}).get('pluginfo', {})
        pluginfo['branch'] = branch

        return PluginDownloadInfo(pluginfo)

    def request(self, uri, method, data, headers={}):
        """Sends a request to the server and returns the response status and data"""

        uri = self.uri + '/' + str(self.apiversion) + '/' + uri.strip('/')
        method = method.upper()
        if method == 'GET':
            if type(data) == dict:
                data = urlencode(data)
            uri += '?%s' % (data)
            data = ''

        if self.ssl:
            r = http.client.HTTPSConnection(self.host)
        else:
            r = http.client.HTTPConnection(self.host)
        logging.debug('%s %s%s' % (method, self.host, uri))
        r.request(method, uri, data, headers)

        resp = r.getresponse()
        if resp.status == 404:
            raise PluginRepositoryNotFoundException()
        elif resp.status != 200:
            raise PluginRepositoryException('Error during the request to the plugin database')

        data = resp.read()
        if len(data) > 0:
            try:
                data = json.loads(data)
            except ValueError:
                raise PluginRepositoryException('Could not parse JSON data. Data received:\n%s' % data)

        return {'status': resp.status, 'data': data}


class PluginRepositoryException(Exception):
    pass


class PluginRepositoryNotFoundException(Exception):
    pass
