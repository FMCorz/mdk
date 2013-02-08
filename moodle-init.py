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

import sys
import os
import argparse
import shutil
import grp
import re
import pwd
import subprocess

from lib.tools import debug, question, get_current_user


def resolve_directory(path, user):
    if path.startswith('~'):
        path = re.sub(r'^~', '~%s' % user, path)
    path = os.path.abspath(os.path.realpath(os.path.expanduser(path)))
    return path

# Arguments
parser = argparse.ArgumentParser(description='Initialise MDK for the current user.')
parser.add_argument('-f', '--force', action='store_true', help='Force the initialisation')
args = parser.parse_args()

# Check root.
if os.getuid() != 0:
    debug('You must execute this as root.')
    debug('  sudo mdk init')
    sys.exit(1)

# Check what user we want to initialise for.
while True:
    username = question('What user are you initialising MDK for?', get_current_user())
    try:
        user = pwd.getpwnam(username)
    except:
        debug('Error while getting information for user %s' % (username))
        continue

    try:
        usergroup = grp.getgrgid(user.pw_gid)
    except:
        debug('Error while getting the group of user %s' % (username))
        continue

    break

# Default directories.
userdir = resolve_directory('~/.moodle-sdk', username)
scriptdir = os.path.dirname(os.path.realpath(__file__))

# Create the main MDK folder.
if not os.path.isdir(userdir):
    debug('Creating directory %s.' % userdir)
    os.mkdir(userdir, 0755)
    os.chown(userdir, user.pw_uid, usergroup.gr_gid)

# Checking if the config file exists.
userconfigfile = os.path.join(userdir, 'config.json')
if os.path.isfile(userconfigfile):
    debug('Config file %s already in place.' % userconfigfile)
    if not args.force:
        debug('Aborting. Use --force to continue.')
        sys.exit(1)
elif not os.path.isfile(userconfigfile):
    debug('Creating user config file in %s.' % userconfigfile)
    shutil.copyfile(os.path.join(scriptdir, 'config-dist.json'), userconfigfile)
    os.chown(userconfigfile, user.pw_uid, usergroup.gr_gid)

# If the group moodle-sdk exists, then we want to add the user to it.
try:
    group = grp.getgrnam('moodle-sdk')
    if not username in group.gr_mem:
        debug('Adding user %s to group %s.' % (username, group.gr_name))
        # This command does not work for some reason...
        # os.initgroups(username, group.gr_gid)
        chgrp = subprocess.Popen(['usermod', '-a', '-G', 'moodle-sdk', username])
        chgrp.wait()
except KeyError:
    # Raised when the group has not been found.
    group = None
    pass

# Loading the configuration.
from lib.config import Conf as Config
C = Config()
C.load(userconfigfile)

# Asks the user what needs to be asked.
while True:
    www = question('What is the DocumentRoot of your virtual host?', C.get('dirs.www'))
    www = resolve_directory(www, username)
    try:
        if not os.path.isdir(www):
            os.mkdir(www, 0775)
            os.chown(www, user.pw_uid, usergroup.gr_gid)
    except:
        debug('Error while creating directory %s' % www)
        continue
    else:
        C.set('dirs.www', www)
        break

while True:
    storage = question('Where do you want to store your Moodle instances?', C.get('dirs.storage'))
    storage = resolve_directory(storage, username)
    try:
        if not os.path.isdir(storage):
            if storage != www:
                os.mkdir(storage, 0775)
                os.chown(storage, user.pw_uid, usergroup.gr_gid)
            else:
                debug('Error! dirs.www and dirs.storage must be different!')
                continue
    except:
        debug('Error while creating directory %s' % storage)
        continue
    else:
        C.set('dirs.storage', storage)
        break

# The default configuration file should point to the right directory for dirs.mdk,
# we will just ensure that it exists.
mdkdir = C.get('dirs.mdk')
mdkdir = resolve_directory(mdkdir, username)
if not os.path.isdir(mdkdir):
    try:
        debug('Creating MDK directory %s' % mdkdir)
        os.mkdir(mdkdir, 0775)
        os.chown(mdkdir, user.pw_uid, usergroup.gr_gid)
    except:
        debug('Error while creating %s, please fix manually.' % mdkdir)

# Git repository.
C.set('remotes.mine', question('What is your remote?', C.get('remotes.mine')))
C.set('myRemote', question('How to name your remote?', C.get('myRemote')))
C.set('upstreamRemote', question('How to name the upsream remote (official Moodle remote)?', C.get('upstreamRemote')))

# Database settings.
C.set('db.mysqli.user', question('What is your MySQL user?', C.get('db.mysqli.user')))
C.set('db.mysqli.passwd', question('What is your MySQL password?', C.get('db.mysqli.passwd')))
C.set('db.pgsql.user', question('What is your PostgreSQL user?', C.get('db.pgsql.user')))
C.set('db.pgsql.passwd', question('What is your PostgreSQL password?', C.get('db.pgsql.passwd')))

debug('')
debug('MDK has been initialised with minimal configuration.')
debug('For more settings, edit your config file: %s.' % userconfigfile)
debug('Use %s as documentation.' % os.path.join(scriptdir, 'config-dist.json'))
debug('')
debug('Type the following command to create your first instance:')
debug('  mdk create')
debug('(This will take some time, but don\'t worry, that\'s because the cache is still empty)')
debug('')
debug('/!\ Please logout/login before to avoid permission issues.')
