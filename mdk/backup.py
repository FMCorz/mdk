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
import json
import time
import logging
from distutils.dir_util import copy_tree

from .tools import chmodRecursive, mkdir
from .db import DB
from .config import Conf
from .workplace import Workplace
from .exceptions import *

C = Conf()
jason = 'info.json'
sqlfile = 'dump.sql'


class BackupManager(object):

    def __init__(self):
        self.path = os.path.expanduser(os.path.join(C.get('dirs.moodle'), 'backup'))
        if not os.path.exists(self.path):
            mkdir(self.path, 0777)

    def create(self, M):
        """Creates a new backup of M"""

        if M.isInstalled() and M.get('dbtype') not in ('mysqli', 'mariadb'):
            raise BackupDBEngineNotSupported('Cannot backup database engine %s' % M.get('dbtype'))

        name = M.get('identifier')
        if name == None:
            raise Exception('Cannot backup instance without identifier!')

        now = int(time.time())
        backup_identifier = self.createIdentifier(name)
        Wp = Workplace()

        # Copy whole directory, shutil will create topath
        topath = os.path.join(self.path, backup_identifier)
        path = Wp.getPath(name)
        logging.info('Copying instance directory')
        copy_tree(path, topath, preserve_symlinks=1)

        # Dump the whole database
        if M.isInstalled():
            logging.info('Dumping database')
            dumpto = os.path.join(topath, sqlfile)
            fd = open(dumpto, 'w')
            M.dbo().selectdb(M.get('dbname'))
            M.dbo().dump(fd)
        else:
            logging.info('Instance not installed. Do not dump database.')

        # Create a JSON file containing all known information
        logging.info('Saving instance information')
        jsonto = os.path.join(topath, jason)
        info = M.info()
        info['backup_origin'] = path
        info['backup_identifier'] = backup_identifier
        info['backup_time'] = now
        json.dump(info, open(jsonto, 'w'), sort_keys=True, indent=4)

        return True

    def createIdentifier(self, name):
        """Creates an identifier"""
        for i in range(1, 100):
            identifier = '{0}_{1:0>2}'.format(name, i)
            if not self.exists(identifier):
                break
            identifier = None
        if not identifier:
            raise Exception('Could not generate a backup identifier! How many backup did you do?!')
        return identifier

    def exists(self, name):
        """Checks whether a backup exists under this name or not"""
        d = os.path.join(self.path, name)
        f = os.path.join(d, jason)
        if not os.path.isdir(d):
            return False
        return os.path.isfile(f)

    def get(self, name):
        return Backup(self.getPath(name))

    def getPath(self, name):
        return os.path.join(self.path, name)

    def list(self):
        """Returns a list of backups with their information"""
        dirs = os.listdir(self.path)
        backups = {}
        for name in dirs:
            if name == '.' or name == '..': continue
            if not self.exists(name): continue
            try:
                backups[name] = Backup(self.getPath(name))
            except:
                # Must successfully retrieve information to be a valid backup
                continue
        return backups


class Backup(object):

    def __init__(self, path):
        self.path = path
        self.jason = os.path.join(path, jason)
        self.sqlfile = os.path.join(path, sqlfile)
        if not os.path.isdir(path):
            raise Exception('Could not find backup in %s' % path)
        elif not os.path.isfile(self.jason):
            raise Exception('Backup information file unfound!')
        self.load()

    def get(self, name):
        """Returns a info on the backup"""
        try:
            return self.infos[name]
        except:
            return None

    def load(self):
        """Loads the backup information"""
        if not os.path.isfile(self.jason):
            raise Exception('Backup information file not found!')
        try:
            self.infos = json.load(open(self.jason, 'r'))
        except:
            raise Exception('Could not load information from JSON file')

    def restore(self, destination=None):
        """Restores the backup"""

        identifier = self.get('identifier')
        if not identifier:
            raise Exception('Identifier is invalid! Cannot proceed.')

        Wp = Workplace()
        if destination == None:
            destination = self.get('backup_origin')
        if not destination:
            raise Exception('Wrong path to perform the restore!')

        if os.path.isdir(destination):
            raise BackupDirectoryExistsException('Destination directory already exists!')

        # Restoring database
        if self.get('installed') and os.path.isfile(self.sqlfile):
            dbname = self.get('dbname')
            dbo = DB(self.get('dbtype'), C.get('db.%s' % self.get('dbtype')))
            if dbo.dbexists(dbname):
                raise BackupDBExistsException('Database already exists!')

        # Copy tree to destination
        try:
            logging.info('Restoring instance directory')
            copy_tree(self.path, destination, preserve_symlinks=1)
            M = Wp.get(identifier)
            chmodRecursive(Wp.getPath(identifier, 'data'), 0777)
        except Exception as e:
            raise Exception('Error while restoring directory\n%s\nto %s. Exception: %s' % (self.path, destination, e))

        # Restoring database
        if self.get('installed') and os.path.isfile(self.sqlfile):
            logging.info('Restoring database')
            content = ''
            f = open(self.sqlfile, 'r')
            for l in f:
                content += l
            queries = content.split(';\n')
            content = None
            logging.info("%d queries to execute" % (len(queries)))

            dbo.createdb(dbname)
            dbo.selectdb(dbname)
            done = 0
            for query in queries:
                if len(query.strip()) == 0: continue
                try:
                    dbo.execute(query)
                except:
                    logging.error('Query failed! You will have to fix this mually. %s', query)
                done += 1
                if done % 500 == 0:
                    logging.debug("%d queries done" % done)
            logging.info('%d queries done' % done)
            dbo.close()

        # Restoring symbolic link
        linkDir = os.path.join(Wp.www, identifier)
        wwwDir = Wp.getPath(identifier, 'www')
        if os.path.islink(linkDir):
            os.remove(linkDir)
        if os.path.isfile(linkDir) or os.path.isdir(linkDir):  # No elif!
            logging.warning('Could not create symbolic link. Please manually create: ln -s %s %s' % (wwwDir, linkDir))
        else:
            os.symlink(wwwDir, linkDir)

        return M
