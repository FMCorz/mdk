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

import os
import json
import httplib
from urllib import urlencode, urlretrieve
import logging
import zipfile
import re
import shutil
from tempfile import gettempdir
from .config import Conf
from . import tools

C = Conf()


class PluginManager(object):

    _subSystems = {
        'admin': '/{admin}',
        'auth': '/auth',
        'availability': '/availability',
        'backup': '/backup/util/ui',
        'badges': '/badges',
        'block': '/blocks',
        'blog': '/blog',
        'cache': '/cache',
        'calendar': '/calendar',
        'cohort': '/cohort',
        'competency': '/competency',
        'course': '/course',
        'editor': '/lib/editor',
        'enrol': '/enrol',
        'files': '/files',
        'form': '/lib/form',
        'grades': '/grade',
        'grading': '/grade/grading',
        'group': '/group',
        'message': '/message',
        'mnet': '/mnet',
        'my': '/my',
        'notes': '/notes',
        'plagiarism': '/plagiarism',
        'portfolio': '/portfolio',
        'publish': '/course/publish',
        'question': '/question',
        'rating': '/rating',
        'register': '/{admin}/registration',
        'repository': '/repository',
        'rss': '/rss',
        'role': '/{admin}/roles',
        'search': '/search',
        'tag': '/tag',
        'user': '/user',
        'webservice': '/webservice'
    }

    _pluginTypesPath = {
        'antivirus': '/lib/antivirus',
        'availability': '/availability/condition',
        'qtype': '/question/type',
        'mod': '/mod',
        'auth': '/auth',
        'calendartype': '/calendar/type',
        'enrol': '/enrol',
        'message': '/message/output',
        'block': '/blocks',
        'filter': '/filter',
        'editor': '/lib/editor',
        'format': '/course/format',
        'profilefield': '/user/profile/field',
        'report': '/report',
        'coursereport': '/course/report',  # Must be after system reports.
        'gradeexport': '/grade/export',
        'gradeimport': '/grade/import',
        'gradereport': '/grade/report',
        'gradingform': '/grade/grading/form',
        'mnetservice': '/mnet/service',
        'webservice': '/webservice',
        'repository': '/repository',
        'portfolio': '/portfolio',
        'search': '/search/engine',
        'qbehaviour': '/question/behaviour',
        'qformat': '/question/format',
        'plagiarism': '/plagiarism',
        'tool': '/{admin}/tool',
        'cachestore': '/cache/stores',
        'cachelock': '/cache/locks',

        'theme': '/theme',
        'local': '/local'
    }
    _supportSubtypes = ['mod', 'editor', 'local', 'tool']

    @classmethod
    def extract(cls, f, plugin, M, override=False):
        """Extract a plugin zip file to the plugin directory of M"""

        if type(plugin) != PluginObject:
            raise ValueError('PluginObject expected')

        if not override and cls.hasPlugin(plugin, M):
            raise Exception('Plugin directory already exists')

        if not cls.validateZipFile(f, plugin.name):
            raise Exception('Invalid zip file')

        zp = zipfile.ZipFile(f)
        try:
            logging.info('Extracting plugin...')
            rootDir = os.path.commonprefix(zp.namelist())
            extractIn = cls.getTypeDirectory(plugin.t, M)
            zp.extractall(extractIn)
            if plugin.name != rootDir.rstrip('/'):
                orig = os.path.join(extractIn, rootDir).rstrip('/')
                dest = os.path.join(extractIn, plugin.name).rstrip('/')

                # Merge directories
                for src_dir, dirs, files in os.walk(orig):
                    dst_dir = src_dir.replace(orig, dest)
                    if not os.path.exists(dst_dir):
                        os.mkdir(dst_dir)
                    for file_ in files:
                        src_file = os.path.join(src_dir, file_)
                        dst_file = os.path.join(dst_dir, file_)
                        if os.path.exists(dst_file):
                            os.remove(dst_file)
                        shutil.move(src_file, dst_dir)

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
    def getSubsystems(cls):
        """Return the list of subsytems and their relative directory"""
        return cls._subSystems

    @classmethod
    def getSubsystemDirectory(cls, subsystem, M=None):
        """Return the subsystem directory, absolute if M is passed"""
        path = cls._subSystems.get(subsystem)
        if not path:
            raise ValueError('Unknown subsystem')

        if M:
            path = path.replace('{admin}', M.get('admin', 'admin'))
            path = os.path.join(M.get('path'), path.strip('/'))

        return path

    @classmethod
    def getSubsystemOrPluginFromPath(cls, path, M=None):
        """Get a subsystem from a path. Path should be relative to dirroot or M should be passed.

        This returns a tuple containing the name of the subsystem or plugin type, and the plugin name
        if we could resolve one.
        """

        subtypes = {}
        path = os.path.realpath(os.path.abspath(path))
        if M:
            path = '/' + path.replace(M.get('path'), '').strip('/')
            admindir = M.get('admin', 'admin')
            if path.startswith('/' + admindir):
                path = re.sub(r'^/%s' % admindir, '/{admin}', path)
            subtypes = cls.getSubtypes(M)
        path = '/' + path.lstrip('/')

        pluginOrSubsystem = None
        pluginName = None
        candidate = path
        head = True
        tail = None
        while head and head != '/' and not pluginOrSubsystem:
            # Check plugin types.
            if not pluginOrSubsystem:
                for k, v in cls._pluginTypesPath.iteritems():
                    if v == candidate:
                        pluginOrSubsystem = k
                        pluginName = tail
                        break

            # Check sub plugin types.
            if not pluginOrSubsystem:
                for k, v in subtypes.iteritems():
                    if v == candidate:
                        pluginOrSubsystem = k
                        pluginName = tail
                        break

            # Check subsystems.
            for k, v in cls._subSystems.iteritems():
                if v == candidate:
                    pluginOrSubsystem = k
                    break

            (head, tail) = os.path.split(candidate)
            candidate = head

        return (pluginOrSubsystem, pluginName)

    @classmethod
    def getSubtypes(cls, M):
        """Get the sub plugins declared in an instance"""
        regex = re.compile(r'\s*(?P<brackets>[\'"])(.*?)(?P=brackets)\s*=>\s*(?P=brackets)(.*?)(?P=brackets)')
        subtypes = {}
        for t in cls._supportSubtypes:
            path = cls.getTypeDirectory(t, M)
            dirs = os.listdir(path)
            for d in dirs:
                if not os.path.isdir(os.path.join(path, d)):
                    continue
                subpluginsfile = os.path.join(path, d, 'db', 'subplugins.php')
                if not os.path.isfile(subpluginsfile):
                    continue

                searchOpen = False
                f = open(subpluginsfile, 'r')
                for line in f:
                    if '$subplugins' in line:
                        searchOpen = True

                    if searchOpen:
                        search = regex.findall(line)
                        if search:
                            for match in search:
                                subtypes[match[1]] = '/' + match[2].replace('admin/', '{admin}/').lstrip('/')

                    # Exit when we find a semi-colon.
                    if searchOpen and ';' in line:
                        break

        return subtypes

    @classmethod
    def getTypeDirectory(cls, t, M=None):
        """Returns the path to the plugin type directory. If M is passed, the full path is returned."""
        path = cls._pluginTypesPath.get(t, False)
        if not path:
            if M:
                subtypes = cls.getSubtypes(M)
                path = subtypes.get(t, False)
            if not path:
                raise ValueError('Unknown plugin or subplugin type')

        if M:
            if t == 'theme':
                themedir = M.get('themedir', None)
                if themedir != None:
                    return themedir

            path = path.replace('{admin}', M.get('admin', 'admin'))
            path = os.path.join(M.get('path'), path.strip('/'))

        return path

    @classmethod
    def hasPlugin(cls, plugin, M):
        path = cls.getTypeDirectory(plugin.t, M)
        target = os.path.join(path, plugin.name)
        return os.path.isdir(target)

    @classmethod
    def validateZipFile(cls, f, name):
        zp = zipfile.ZipFile(f, 'r')

        # Checking that the content is all contained in one single directory
        rootDir = os.path.commonprefix(zp.namelist())
        if rootDir == '':
            return False
        return True


class PluginObject(object):

    component = None
    t = None
    name = None

    def __init__(self, component):
        self.component = component
        (self.t, self.name) = PluginManager.getTypeAndName(component)
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

        if not 'downloadurl' in self.keys():
            raise ValueError('Expecting the key downloadurl')
        elif not 'component' in self.keys():
            raise ValueError('Expecting the key component')
        elif not 'branch' in self.keys():
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
                tools.mkdir(dest, 0777)

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

    def info(self, plugin, branch):
        """Gets the download information of the plugin, branch is expected to be
        a whole integer, such as 25 for 2.5, etc...
        """

        if type(branch) != int:
            raise ValueError('Branch must be an integer')

        # Checking local repository
        lr = self.localRepository.get(plugin, False)
        if lr:
            info = lr.get(branch, None)
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
                return PluginDownloadInfo(info)

        # Contacting the remote repository
        data = {
            "branch": round(float(branch) / 10., 1),
            "plugin": plugin
        }

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
            r = httplib.HTTPSConnection(self.host)
        else:
            r = httplib.HTTPConnection(self.host)
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
