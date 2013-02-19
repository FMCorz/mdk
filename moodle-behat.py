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
import argparse
import os
import urllib
import re
from time import sleep
from lib import workplace
from lib.tools import debug, process, ProcessInThread
from lib.config import Conf

C = Conf()

# Arguments
parser = argparse.ArgumentParser(description='Initialise Behat')
parser.add_argument('-r', '--run', action='store_true', help='run the tests')
parser.add_argument('-j', '--no-javascript', action='store_true', help='skip the tests involving Javascript', dest='nojavascript')
parser.add_argument('-s', '--switch-completely', action='store_true', help='force the switch completely setting. This will be automatically enabled for PHP < 5.4', dest='switchcompletely')
parser.add_argument('--selenium', metavar='jarfile', nargs='?', default=None, help='path to the selenium standalone server to use', dest='selenium')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

Wp = workplace.Workplace(C.get('dirs.storage'))

# Loading instance
M = Wp.resolve(args.name)
if not M:
    debug('This is not a Moodle instance')
    sys.exit(1)

# Check if installed
if not M.get('installed'):
    debug('This instance needs to be installed first')
    sys.exit(1)

# If not composer.phar, install Composer
if not os.path.isfile(os.path.join(M.get('path'), 'composer.phar')):
    debug('Installing Composer')
    cliFile = 'behat_install_composer.php'
    cliPath = os.path.join(M.get('path'), 'behat_install_composer.php')
    urllib.urlretrieve('http://getcomposer.org/installer', cliPath)
    M.cli('/' + cliFile, stdout=None)
    os.remove(cliPath)
    M.cli('composer.phar', args='install --dev')

# Download selenium
seleniumPath = os.path.expanduser(os.path.join(C.get('dirs.mdk'), 'selenium.jar'))
if args.selenium:
    seleniumPath = args.selenium
elif not os.path.isfile(seleniumPath):
    debug('Attempting to find a download for Selenium')
    url = urllib.urlopen('http://docs.seleniumhq.org/download/')
    content = url.read()
    selenium = re.search(r'http:[a-z0-9/._-]+selenium-server-standalone-[0-9.]+\.jar', content, re.I)
    if selenium:
        debug('Downloading Selenium from %s' % (selenium.group(0)))
        urllib.urlretrieve(selenium.group(0), seleniumPath)
    else:
        debug('Could not locate Selenium server to download')

if not os.path.isfile(seleniumPath):
    debug('Selenium file %s does not exist')
    sys.exit(1)

# Run cli
try:
    M.initBehat(switchcompletely=args.switchcompletely)
    debug('Behat ready!')

    # Preparing Behat command
    cmd = ['vendor/bin/behat']
    if args.nojavascript:
        cmd.append('--tags ~@javascript')
    cmd.append('--config=%s/behat/behat.yml' % (M.get('behat_dataroot')))
    cmd = ' '.join(cmd)

    if args.run:
        debug('Preparing Behat testing')

        # Preparing PHP Server
        phpServer = None
        if not M.get('behat_switchcompletely'):
            debug('Starting standalone PHP server')
            phpServer = ProcessInThread('%s -S http://localhost:8000' % (C.get('php')))
            phpServer.start()

        # Launching Selenium
        seleniumServer = None
        if seleniumPath and not args.nojavascript:
            debug('Starting Selenium server')
            seleniumServer = ProcessInThread('%s -jar %s' % (C.get('java'), seleniumPath))
            seleniumServer.start()

        debug('Running Behat tests')

        # Sleep for a few seconds before starting Behat
        if phpServer or seleniumServer:
            sleep(3)

        # Running the tests
        process(cmd, M.path, None, None)

        # Kill the remaining processes
        if phpServer:
            phpServer.kill()
        if seleniumServer:
            seleniumServer.kill()

        # Remove the switch completely tag
        if M.get('behat_switchcompletely'):
            M.updateConfig('behat_switchcompletely', False)

    else:
        debug('Behat command: %s' % (cmd))

except Exception as e:
    debug(e)
    sys.exit(1)
