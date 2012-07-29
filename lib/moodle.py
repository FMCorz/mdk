#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from tools import debug
from db import DB
from config import Conf

C = Conf().get

class Moodle():

    path = None
    installed = False
    settings = {}

    _dbo = None
    _loaded = False

    def __init__(self, path):
        self.path = path
        self._load()

    def dbo(self):
        if self._dbo == None:
            engine = self.get('dbtype')
            db = self.get('dbname')
            if engine != None and db != None:
                try:
                    self._dbo = DB(engine, C('db.%s' % engine))
                except:
                    pass
        return self._dbo

    def get(self, param, default = None):
        info = self.info()
        try:
            return info[param]
        except:
            return default

    def info(self):
        self._load()
        info = self.settings.copy()
        info['path'] = self.path
        info['installed'] = self.installed
        return info

    @staticmethod
    def isInstance(path):
        version = os.path.join(path, 'version.php')
        try:
            f = open(version, 'r')
            lines = f.readlines()
            f.close()
        except:
            return False
        found = False
        for line in lines:
            if line.find('MOODLE VERSION INFORMATION') > -1:
                found = True
                break
        if not found:
            return False

        return True

    def _load(self):

        if self._loaded:
            return True

        config = os.path.join(self.path, 'config.php')
        if not os.path.isfile(config):
            return None

        # Extracts parameters from config.php, does not handle params over multiple lines
        prog = re.compile('^\s*\$CFG->([a-z]+)\s*=\s*(?P<brackets>[\'"])(.+)(?P=brackets)\s*;$', re.I)
        try:
            f = open(config, 'r')
            for line in f:
                match = prog.search(line)
                if match == None: continue
                self.settings[match.group(1)] = match.group(3)
            f.close()

        except Exception as e:
            debug('Error while reading config file')

        self._loaded = True
        return True

    def reload(self):
        self._loaded = False
        return self._load()

