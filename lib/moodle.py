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
import re
import shutil

from tools import debug, process
from db import DB
from config import Conf
from git import Git
from exceptions import ScriptNotFound

C = Conf()


class Moodle(object):

    identifier = None
    path = None
    installed = False
    version = None
    config = None

    _dbo = None
    _git = None
    _loaded = False

    _cos_hasstash = False
    _cos_oldbranch = None

    def __init__(self, path, identifier = None):
        self.path = path
        self.identifier = identifier
        self.version = {}
        self.config = {}
        self._load()

    def addConfig(self, name, value):
        """Add a parameter to the config file"""
        configFile = os.path.join(self.path, 'config.php')
        if not os.path.isfile(configFile):
            return None

        if type(value) != 'int':
            value = "'" + str(value) + "'"
        value = str(value)

        try:
            f = open(configFile, 'a')
            f.write('\n$CFG->%s = %s;' % (name, value))
            f.close()
        except:
            raise Exception('Error while writing to config file')

    def branch_compare(self, branch, compare = '>='):
        """Compare the branch of the current instance with the one passed"""
        try:
            branch = int(branch)
        except:
            raise Exception('Could not convert branch to int, got %s' % branch)
        b = self.get('branch')
        if b == None:
            raise Exception('Error while reading the branch')
        elif b == 'master':
            b = C.get('masterBranch')
        b = int(b)
        if compare == '>=':
            return b >= branch
        elif compare == '>':
            return b > branch
        elif compare == '=' or compare == '==':
            return b == branch
        if compare == '<=':
            return b <= branch
        elif compare == '<':
            return b < branch
        return False

    def checkout_stable(self, checkout = True):
        """Checkout the stable branch, do a stash if required. Needs to be called again to pop the stash!"""

        # Checkout the branch
        if checkout:
            stablebranch = self.get('stablebranch')
            if self.currentBranch() == stablebranch:
                self._cos_oldbranch = None
                return True

            self._cos_oldbranch = self.currentBranch()
            self._cos_hasstash = False

            # Stash
            stash = self.git().stash(untracked=True)
            if stash[0] != 0:
                raise Exception('Error while stashing your changes')
            if not stash[1].startswith('No local changes'):
                self._cos_hasstash = True

            # Checkout STABLE
            if not self.git().checkout(stablebranch):
                raise Exception('Could not checkout %s' % stablebranch)

        # Checkout the previous branch
        elif self._cos_oldbranch != None:
            if not self.git().checkout(self._cos_oldbranch):
                raise Exception('Could not checkout working branch %s' % self._cos_oldbranch)

            # Unstash
            if self._cos_hasstash:
                pop = self.git().stash('pop')
                if pop[0] != 0:
                    raise Exception('Error while popping the stash. Probably got conflicts.')
                self._cos_hasstash = False

    def cli(self, cli, args = '', **kwargs):
        """Executes a command line tool script"""
        cli = os.path.join(self.get('path'), cli.lstrip('/'))
        if not os.path.isfile(cli):
            raise Exception('Could not find script to call')
        if type(args) == 'list':
            args = ' '.join(args)
        cmd = '%s %s %s' % (C.get('php'), cli, args)
        return process(cmd, cwd=self.get('path'), **kwargs)

    def currentBranch(self):
        """Returns the current branch on the git repository"""
        return self.git().currentBranch()

    def dbo(self):
        """Returns a Database object"""
        if self._dbo == None:
            engine = self.get('dbtype')
            db = self.get('dbname')
            if engine != None and db != None:
                try:
                    self._dbo = DB(engine, C.get('db.%s' % engine))
                except:
                    pass
        return self._dbo

    def generateBranchName(self, issue, suffix='', version=''):
        """Generates a branch name"""
        mdl = re.sub(r'MDL(-|_)?', '', issue, flags=re.I)
        if version == '':
            version = self.get('branch')
        args = {
            'issue': mdl,
            'version': version
        }
        branch = C.get('wording.branchFormat') % args
        if suffix != None and suffix != '':
            branch += C.get('wording.branchSuffixSeparator') + suffix
        return branch

    def get(self, param, default = None):
        """Returns a property of this instance"""
        info = self.info()
        try:
            return info[param]
        except:
            return default

    def git(self):
        """Returns a Git object"""
        if self._git == None:
            self._git = Git(self.path, C.get('git'))
            if not self._git.isRepository():
                raise Exception('Could not find the Git repository')
        return self._git

    def initPHPUnit(self):
        """Initialise the PHP Unit environment"""

        if self.branch_compare(23, '<'):
            raise Exception('PHP Unit is only available from Moodle 2.3')

        # Set PHP Unit data root
        phpunit_dataroot = self.get('dataroot') + '_phpu'
        if self.get('phpunit_dataroot') == None:
            self.addConfig('phpunit_dataroot', phpunit_dataroot)
        elif self.get('phpunit_dataroot') != phpunit_dataroot:
            raise Exception('Excepted value for phpunit_dataroot is \'%s\'' % phpunit_dataroot)
        if not os.path.isdir(phpunit_dataroot):
            os.mkdir(phpunit_dataroot, 0777)

        # Set PHP Unit prefix
        phpunit_prefix = 'phpu_'
        if self.get('phpunit_prefix') == None:
            self.addConfig('phpunit_prefix', phpunit_prefix)
        elif self.get('phpunit_prefix') != phpunit_prefix:
            raise Exception('Excepted value for phpunit_prefix is \'%s\'' % phpunit_prefix)

        result = (None, None, None)
        exception = False
        try:
            result = self.cli('/admin/tool/phpunit/cli/init.php', stdout = None, stderr = None)
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
        """Returns a dictionary of information about this instance"""
        self._load()
        info = {
            'path': self.path,
            'installed': self.isInstalled(),
            'identifier': self.identifier
        }
        for (k, v) in self.config.items():
            info[k] = v
        for (k, v) in self.version.items():
            info[k] = v
        return info

    def install(self, dbname = None, engine = None, dataDir = None, fullname = None, dropDb = False):
        """Launch the install script of an Instance"""

        if self.isInstalled():
            raise Exception('Instance already installed!')

        if dataDir == None or not os.path.isdir(dataDir):
            raise Exception('Cannot install instance without knowing where the data directory is')
        if dbname == None:
            dbname = re.sub(r'[^a-zA-Z0-9]', '', self.identifier).lower()[:28]
        if engine == None:
            engine = C.get('defaultEngine')
        if fullname == None:
            fullname = self.identifier.replace('-', ' ').replace('_', ' ').title()
            fullname = fullname + ' ' + C.get('wording.%s' % engine)

        debug('Creating database...')
        db = DB(engine, C.get('db.%s' % engine))
        if db.dbexists(dbname):
            if dropDb:
                db.dropdb(dbname)
                db.createdb(dbname)
            else:
                raise Exception('Cannot install an instance on an existing database (%s)' % dbname)
        else:
            db.createdb(dbname)
        db.selectdb(dbname)

        # Defining wwwroot.
        wwwroot = 'http://%s/' % C.get('host')
        if C.get('path') != '' and C.get('path') != None:
            wwwroot = wwwroot + C.get('path') + '/'
        wwwroot = wwwroot + self.identifier

        debug('Installing %s...' % self.identifier)
        cli = 'admin/cli/install.php'
        params = (wwwroot, dataDir, engine, dbname, C.get('db.%s.user' % engine), C.get('db.%s.passwd' % engine), C.get('db.%s.host' % engine), fullname, self.identifier, C.get('login'), C.get('passwd'))
        args = '--wwwroot="%s" --dataroot="%s" --dbtype="%s" --dbname="%s" --dbuser="%s" --dbpass="%s" --dbhost="%s" --fullname="%s" --shortname="%s" --adminuser="%s" --adminpass="%s" --allow-unstable --agree-license --non-interactive' % params
        result = self.cli(cli, args, stdout=None, stderr=None)
        if result[0] != 0:
            raise Exception('Error while running the install, please manually fix the problem.')

        configFile = os.path.join(self.path, 'config.php')
        os.chmod(configFile, 0666)
        try:
            self.addConfig('sessioncookiepath', '/%s/' % self.identifier)
        except Exception as e:
            debug('Could not append $CFG->sessioncookiepath to config.php')

        self.reload()

    def isInstalled(self):
        """Returns whether this instance is installed or not"""
        return self.installed == True

    @staticmethod
    def isInstance(path):
        """Check whether the path is a Moodle web directory"""
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

    def isIntegration(self):
        """Returns whether an instance is an integration one or not"""
        r = C.get('upstreamRemote') or 'upstream'
        if not self.git().getRemote(r):
            r = 'origin'
        remote = self.git().getConfig('remote.%s.url' % r)
        if remote != None and remote.endswith('integration.git'):
            return True
        return False

    def isStable(self):
        """Assume an instance is stable if not integration"""
        return not self.isIntegration()

    def _load(self):
        """Loads the information"""
        if not self.isInstance(self.path):
            return False

        if self._loaded:
            return True

        # Extracts information from version.php
        self.version = {}
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
            if int(branch) >= int(C.get('masterBranch')):
                self.version['branch'] = 'master'

            # Stable branch
            if self.version['branch'] == 'master':
                self.version['stablebranch'] = 'master'
            else:
                self.version['stablebranch'] = 'MOODLE_%s_STABLE' % self.version['branch']

            # Integration or stable?
            self.version['integration'] = self.isIntegration()

            f.close()
        else:
            # Should never happen
            raise Exception('This does not appear to be a Moodle instance')

        # Extracts parameters from config.php, does not handle params over multiple lines
        self.config = {}
        config = os.path.join(self.path, 'config.php')
        if os.path.isfile(config):
            self.installed = True
            prog = re.compile(r'^\s*\$CFG->([a-z_]+)\s*=\s*(?P<brackets>[\'"])(.+)(?P=brackets)\s*;$', re.I)
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

    def purge(self):
        """Purge the cache of an instance"""
        if not self.isInstalled():
            raise Exception('Instance not installed, cannot purge.')
        elif self.branch_compare('22', '<'):
            raise Exception('Instance does not support cache purging.')

        try:
            self.cli('admin/cli/purge_caches.php', stderr=None, stdout=None)
        except Exception as e:
            raise Exception('Error while purging cache!')

    def reload(self):
        """Reloads the information"""
        self._loaded = False
        return self._load()

    def runScript(self, scriptname, **kwargs):
        """Runs a script on the instance"""
        supported = ['php']
        directories = ['~/.moodle-sdk']
        if C.get('dirs.moodle') != None:
            directories.insert(0, C.get('dirs.moodle'))
        directories.append('/etc/moodle-sdk')
        directories.append(os.path.join(os.path.dirname(__file__), '..'))

        # Loop over each directory in order of preference.
        for directory in directories:
            script = None
            type = None

            f = os.path.expanduser(os.path.join(directory, 'scripts', scriptname))
            if os.path.isfile(f) and scriptname.rsplit('.', 1)[1] in supported:
                script = f
                type = scriptname.rsplit('.', 1)[1]
            else:
                for ext in supported:
                    print f + '.' + ext
                    if os.path.isfile(f + '.' + ext):
                        script = f + '.' + ext
                        type = ext
                        break
            # Exit the loop if the script has been found.
            if script != None and type != None:
                break

        if not script:
            raise ScriptNotFound('Could not find the script, or format not supported')

        if type == 'php':
            dest = os.path.join(self.get('path'), 'mdkrun.php')
            shutil.copyfile(script, dest)
            result = self.cli('mdkrun.php', **kwargs)
            os.remove(dest)
            return result[0]

    def update(self, remote = None):
        """Update the instance from the remote"""

        if remote == None:
            remote = C.get('upstreamRemote')

        # Fetch
        if not self.git().fetch(remote):
            raise Exception('Could not fetch remote %s' % remote)

        # Checkout stable
        self.checkout_stable(True)

        # Reset HARD
        upstream = '%s/%s' % (remote, self.get('stablebranch'))
        if not self.git().reset(to = upstream, hard = True):
            raise Exception('Error while executing git reset.')

        # Return to previous branch
        self.checkout_stable(False)

    def upgrade(self, nocheckout = False):
        """Calls the upgrade script"""
        if not self.isInstalled():
            raise Exception('Cannot upgrade an instance which is not installed.')
        elif not self.branch_compare(20):
            raise Exception('Upgrade command line tool not supported by this version.')

        # Checkout stable
        if not nocheckout:
            self.checkout_stable(True)

        cli = '/admin/cli/upgrade.php'
        args = '--non-interactive --allow-unstable'
        result = self.cli(cli, args, stdout = None, stderr = None)
        if result[0] != 0:
            raise Exception('Error while running the upgrade.')

        # Return to previous branch
        if not nocheckout:
            self.checkout_stable(False)
