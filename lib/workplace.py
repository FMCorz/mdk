#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

from tools import debug
import config
import db
import moodle

C = config.Conf().get

class Workplace():

    def __init__(self, path = None, wwwDir = None, dataDir = None):
        if path == None:
            path = C('dirs.store')
        if wwwDir == None:
            wwwDir = C('wwwDir')
        if dataDir == None:
            dataDir = C('dataDir')

        if not os.path.isdir(path):
            raise Exception('Directory %s not found' % path)

        self.path = os.path.abspath(os.path.realpath(path))
        self.wwwDir = wwwDir
        self.dataDir = dataDir

    def delete(self, name):
        # Instantiating the object also checks if it exists
        M = self.get(name)
        DB = M.dbo()
        dbname = M.get('dbname')

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
        if DB and dbname:
            DB.dropdb(dbname)

    def get(self, name):

        # Extracts name from path
        if os.sep in name:
            path = os.path.abspath(os.path.realpath(name))
            if not path.startswith(self.path):
                raise Exception('Could not find Moodle instance at %s' % name)
            (head, name) = os.path.split(path)

        if not self.isMoodle(name):
            raise Exception('Could not find Moodle instance %s' % name)
        return moodle.Moodle(os.path.join(self.path, name, self.wwwDir), identifier = name)

    def isMoodle(self, name):
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
        dirs = os.listdir(self.path)
        names = []
        for d in dirs:
            if d == '.' or d == '..': continue
            if not os.path.isdir(os.path.join(self.path, d)): continue
            if not self.isMoodle(d): continue
            names.append(d)
        return names

