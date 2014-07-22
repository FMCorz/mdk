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
import grp
import re
import pwd
import subprocess
import logging

from ..command import Command
from ..tools import question, get_current_user, mkdir


class InitCommand(Command):

    _arguments = [
        (
            ['-f', '--force'],
            {
                'action': 'store_true',
                'help': 'Force the initialisation'
            }
        )
    ]
    _description = 'Initialise MDK'

    def resolve_directory(self, path, user):
        if path.startswith('~'):
            path = re.sub(r'^~', '~%s' % user, path)
        path = os.path.abspath(os.path.realpath(os.path.expanduser(path)))
        return path

    def run(self, args):

        # Check what user we want to initialise for.
        while True:
            username = question('What user are you initialising MDK for?', get_current_user())
            try:
                user = pwd.getpwnam(username)
            except:
                logging.warning('Error while getting information for user %s' % (username))
                continue

            try:
                usergroup = grp.getgrgid(user.pw_gid)
            except:
                logging.warning('Error while getting the group of user %s' % (username))
                continue

            break

        # Default directories.
        userdir = self.resolve_directory('~/.moodle-sdk', username)
        scriptdir = os.path.dirname(os.path.realpath(__file__))

        # Create the main MDK folder.
        if not os.path.isdir(userdir):
            logging.info('Creating directory %s.' % userdir)
            mkdir(userdir, 0755)
            os.chown(userdir, user.pw_uid, usergroup.gr_gid)

        # Checking if the config file exists.
        userconfigfile = os.path.join(userdir, 'config.json')
        if os.path.isfile(userconfigfile):
            logging.info('Config file %s already in place.' % userconfigfile)
            if not args.force:
                raise Exception('Aborting. Use --force to continue.')

        elif not os.path.isfile(userconfigfile):
            logging.info('Creating user config file in %s.' % userconfigfile)
            open(userconfigfile, 'w')
            os.chown(userconfigfile, user.pw_uid, usergroup.gr_gid)

        # Loading the configuration.
        from ..config import Conf as Config
        C = Config(userfile=userconfigfile)

        # Asks the user what needs to be asked.
        while True:
            www = question('What is the DocumentRoot of your virtual host?', C.get('dirs.www'))
            www = self.resolve_directory(www, username)
            try:
                if not os.path.isdir(www):
                    mkdir(www, 0775)
                    os.chown(www, user.pw_uid, usergroup.gr_gid)
            except:
                logging.error('Error while creating directory %s' % www)
                continue

            if not os.access(www, os.W_OK):
                logging.error('You need to have permission to write to that directory.\nPlease fix or use another directory.')
                continue

            C.set('dirs.www', www)
            break

        while True:
            storage = question('Where do you want to store your Moodle instances?', C.get('dirs.storage'))
            storage = self.resolve_directory(storage, username)
            try:
                if not os.path.isdir(storage):
                    if storage != www:
                        mkdir(storage, 0775)
                        os.chown(storage, user.pw_uid, usergroup.gr_gid)
                    else:
                        logging.error('Error! dirs.www and dirs.storage must be different!')
                        continue
            except:
                logging.error('Error while creating directory %s' % storage)
                continue

            if not os.access(storage, os.W_OK):
                logging.error('You need to have permission to write to that directory.\nPlease fix or use another directory.')
                continue

            C.set('dirs.storage', storage)
            break

        # The default configuration file should point to the right directory for dirs.mdk,
        # we will just ensure that it exists.
        mdkdir = C.get('dirs.mdk')
        mdkdir = self.resolve_directory(mdkdir, username)
        if not os.path.isdir(mdkdir):
            try:
                logging.info('Creating MDK directory %s' % mdkdir)
                mkdir(mdkdir, 0775)
                os.chown(mdkdir, user.pw_uid, usergroup.gr_gid)
            except:
                logging.error('Error while creating %s, please fix manually.' % mdkdir)

        # Git repository.
        github = question('What is your Github username? (Leave blank if not using Github)')
        if github != None:
            C.set('remotes.mine', C.get('remotes.mine').replace('YourGitHub', github))
            C.set('repositoryUrl', C.get('repositoryUrl').replace('YourGitHub', github))
            C.set('diffUrlTemplate', C.get('diffUrlTemplate').replace('YourGitHub', github))
            C.set('myRemote', 'github')
            C.set('upstreamRemote', 'origin')
        else:
            C.set('remotes.mine', question('What is your remote?', C.get('remotes.mine')))
            C.set('myRemote', question('What to call your remote?', C.get('myRemote')))
            C.set('upstreamRemote', question('What to call the upsream remote (official Moodle remote)?', C.get('upstreamRemote')))

        # Database settings.
        C.set('db.mysqli.user', question('What is your MySQL user?', C.get('db.mysqli.user')))
        C.set('db.mysqli.passwd', question('What is your MySQL password?', 'root', password=True))
        C.set('db.pgsql.user', question('What is your PostgreSQL user?', C.get('db.pgsql.user')))
        C.set('db.pgsql.passwd', question('What is your PostgreSQL password?', 'root', password=True))

        print ''
        print 'MDK has been initialised with minimal configuration.'
        print 'For more settings, edit your config file: %s.' % userconfigfile
        print 'Use %s as documentation.' % os.path.join(scriptdir, 'config-dist.json')
        print ''
        print 'Type the following command to create your first instance:'
        print '  mdk create'
        print '(This will take some time, but don\'t worry, that\'s because the cache is still empty)'
        print ''
        print '/!\ Please logout/login before to avoid permission issues: sudo su `whoami`'
