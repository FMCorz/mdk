#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import subprocess

from tools import debug
from db import DB
from config import Conf
from git import Git

C = Conf().get

class Moodle():

    path = None
    installed = False
    version = {}
    config = {}

    _dbo = None
    _git = None
    _loaded = False

    def __init__(self, path):
        self.path = path
        self._load()

    def addConfig(self, name, value):
        if not self.get('installed'):
            return None

        if type(value) != 'int':
            value = "'" + str(value) + "'"
        value = str(value)

        try:
            f = open(os.path.join(self.path, 'config.php'), 'a+')
            f.write('\n$CFG->%s = %s;' % (name, value))
            f.close()
        except:
            raise Exception('Error while writing to config file')

    def branch(self):
        return self._git().currentBranch()

    def cli(self, cli):
        cli = os.path.join(self.get('path'), cli.lstrip('/'))
        if not os.path.isfile(cli):
            raise Exception('Could not find script to call')
        proc = subprocess.Popen([C('php'), cli], cwd=self.get('path'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()
        return (proc.returncode, stdout, stderr)

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

    def git(self):
        if self._git == None:
            self._git = Git(self.path, C('git'))
        return self._git

    def initPHPUnit(self):
        result = (None, None, None)
        exception = False
        try:
            result = self.cli('/admin/tool/phpunit/cli/init.php')
        except Exception as e:
            exception = True

        if exception or result[0] > 0:
            if result[0] == 129:
                raise Exception('PHP Unit is not installed on your system')
            elif result[0] > 0:
                raise Exception('Something wrong with PHP Unit configuration')
            else:
                raise Exception('Error while calling PHP Unit init script')

    def info(self):
        self._load()
        info = {}
        info['path'] = self.path
        info['installed'] = self.installed
        for (k, v) in self.config.items():
            info[k] = v
        for (k, v) in self.version.items():
            info[k] = v
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

        if not self.isInstance(self.path):
            return False

        if self._loaded:
            return True

        # Extracts information from version.php
        version = os.path.join(self.path, 'version.php')
        if os.path.isfile(version):

            reVersion = re.compile(r'^\s*\$version\s*=\s*([0-9.]+)\s*;')
            reRelease = re.compile(r'^\s*\$release\s*=\s*(?P<brackets>[\'"])?(.+)(?P=brackets)\s*;')
            reMaturity = re.compile(r'^\s*\$maturity\s*=\s*([a-zA-Z0-9_]+)\s*;')
            reBranch = re.compile(r'^\s*\$branch\s*=\s*(?P<brackets>[\'"])?([0-9]+)(?P=brackets)\s*;')

            f = open(version, 'r')
            for line in f:
                if reVersion.search(line):
                    self.version['version'] = reVersion.search(line).group(1)
                elif reRelease.search(line):
                    self.version['release'] = reRelease.search(line).group(2)
                elif reMaturity.search(line):
                    self.version['maturity'] = reMaturity.search(line).group(1).replace('MATURITY_', '').lower()
                elif reBranch.search(line):
                    self.version['branch'] = reBranch.search(line).group(2)

            # Several checks about the branch
            try:
                # Has it been set?
                branch = self.version['branch']
            except:
                self.version['branch'] = self.version['release'].replace('.', '')[0:2]
                branch = self.version['branch']
            if int(branch) >= int(C('masterBranch')):
                self.version['branch'] = 'master'

            # Stable branch
            if self.version['branch'] == 'master':
                self.version['stablebranch'] = 'master'
            else:
                self.version['stablebranch'] = 'MOODLE_%s_STABLE' % self.version['branch']

            f.close()
        else:
            # Should never happen
            raise Exception('This does not appear to be a Moodle instance')

        # Extracts parameters from config.php, does not handle params over multiple lines
        config = os.path.join(self.path, 'config.php')
        if os.path.isfile(config):
            self.installed = True
            prog = re.compile(r'^\s*\$CFG->([a-z]+)\s*=\s*(?P<brackets>[\'"])(.+)(?P=brackets)\s*;$', re.I)
            try:
                f = open(config, 'r')
                for line in f:
                    match = prog.search(line)
                    if match == None: continue
                    self.config[match.group(1)] = match.group(3)
                f.close()

            except Exception as e:
                debug('Error while reading config file')
        else:
            self.installed = False

        self._loaded = True
        return True

    def reload(self):
        self._loaded = False
        return self._load()

