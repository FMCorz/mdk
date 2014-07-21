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
import urllib
import re
import logging
import gzip
from time import sleep
from ..command import Command
from ..tools import process, ProcessInThread, downloadProcessHook


class BehatCommand(Command):

    _arguments = [
        (
            ['-r', '--run'],
            {
                'action': 'store_true',
                'help': 'run the tests'
            }
        ),
        (
            ['-d', '--disable'],
            {
                'action': 'store_true',
                'help': 'disable Behat, runs the tests first if --run has been set. Ignored from 2.7.'
            }
        ),
        (
            ['-f', '--feature'],
            {
                'metavar': 'path',
                'help': 'typically a path to a feature, or an argument understood by behat (see [features]: vendor/bin/behat --help). Automatically convert path to absolute path.'
            }
        ),
        (
            ['-n', '--testname'],
            {
                'dest': 'testname',
                'metavar': 'name',
                'help': 'only execute the feature elements which match part of the given name or regex'
            }
        ),
        (
            ['-t', '--tags'],
            {
                'metavar': 'tags',
                'help': 'only execute the features or scenarios with tags matching tag filter expression'
            }
        ),
        (
            ['-j', '--no-javascript'],
            {
                'action': 'store_true',
                'dest': 'nojavascript',
                'help': 'do not start Selenium and ignore Javascript (short for --tags=~@javascript). Cannot be combined with --tags or --testname.'
            }
        ),
        (
            ['-s', '--switch-completely'],
            {
                'action': 'store_true',
                'dest': 'switchcompletely',
                'help': 'force the switch completely setting. This will be automatically enabled for PHP < 5.4. Ignored from 2.7.'
            }
        ),
        (
            ['--selenium'],
            {
                'default': None,
                'dest': 'selenium',
                'help': 'path to the selenium standalone server to use',
                'metavar': 'jarfile'
            }
        ),
        (
            ['--selenium-download'],
            {
                'action': 'store_true',
                'dest': 'seleniumforcedl',
                'help': 'force the download of the latest Selenium to the cache'
            }
        ),
        (
            ['--selenium-verbose'],
            {
                'action': 'store_true',
                'dest': 'seleniumverbose',
                'help': 'outputs the output from selenium in the same window'
            }
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name',
                'nargs': '?'
            }
        )
    ]
    _description = 'Initialise Behat'

    def run(self, args):

        # Loading instance
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        # Check required version
        if M.branch_compare(25, '<'):
            raise Exception('Behat is only available from Moodle 2.5')

        # Check if installed
        if not M.get('installed'):
            raise Exception('This instance needs to be installed first')

        # Disable Behat
        if args.disable and not args.run:
            self.disable(M)
            return

        # No Javascript
        nojavascript = args.nojavascript
        if not nojavascript and not self.C.get('java') or not os.path.isfile(os.path.abspath(self.C.get('java'))):
            nojavascript = True
            logging.info('Disabling Javascript because Java is required to run Selenium and could not be found.')

        # If not composer.phar, install Composer
        if not os.path.isfile(os.path.join(M.get('path'), 'composer.phar')):
            logging.info('Installing Composer')
            cliFile = 'behat_install_composer.php'
            cliPath = os.path.join(M.get('path'), 'behat_install_composer.php')
            (to, headers) = urllib.urlretrieve('http://getcomposer.org/installer', cliPath)
            if headers.dict.get('content-encoding') == 'gzip':
                f = gzip.open(cliPath, 'r')
                content = f.read()
                f.close()
                f = open(cliPath, 'w')
                f.write(content)
                f.close()
            M.cli('/' + cliFile, stdout=None, stderr=None)
            os.remove(cliPath)
            M.cli('composer.phar', args='install --dev', stdout=None, stderr=None)

        # Download selenium
        seleniumPath = os.path.expanduser(os.path.join(self.C.get('dirs.mdk'), 'selenium.jar'))
        if args.selenium:
            seleniumPath = args.selenium
        elif args.seleniumforcedl or (not nojavascript and not os.path.isfile(seleniumPath)):
            logging.info('Attempting to find a download for Selenium')
            url = urllib.urlopen('http://docs.seleniumhq.org/download/')
            content = url.read()
            selenium = re.search(r'http:[a-z0-9/._-]+selenium-server-standalone-[0-9.]+\.jar', content, re.I)
            if selenium:
                logging.info('Downloading Selenium from %s' % (selenium.group(0)))
                if (logging.getLogger().level <= logging.INFO):
                    urllib.urlretrieve(selenium.group(0), seleniumPath, downloadProcessHook)
                    # Force a new line after the hook display
                    logging.info('')
                else:
                    urllib.urlretrieve(selenium.group(0), seleniumPath)
            else:
                logging.warning('Could not locate Selenium server to download')

        if not nojavascript and not os.path.isfile(seleniumPath):
            raise Exception('Selenium file %s does not exist')

        # Run cli
        try:
            logging.info('Initialising Behat, please be patient!')
            M.initBehat(switchcompletely=args.switchcompletely)
            logging.info('Behat ready!')

            # Preparing Behat command
            cmd = ['vendor/bin/behat']
            if args.tags:
                cmd.append('--tags="%s"' % (args.tags))

            if args.testname:
                cmd.append('--name="%s"' % (args.testname))

            if not (args.tags or args.testname) and nojavascript:
                cmd.append('--tags ~@javascript')

            cmd.append('--config=%s/behat/behat.yml' % (M.get('behat_dataroot')))

            # Checking feature argument
            if args.feature:
                filepath = args.feature
                if not filepath.startswith('/'):
                    filepath = os.path.join(M.get('path'), filepath)
                cmd.append(filepath)

            cmd = ' '.join(cmd)

            phpCommand = '%s -S localhost:8000' % (self.C.get('php'))
            seleniumCommand = None
            if seleniumPath:
                seleniumCommand = '%s -jar %s' % (self.C.get('java'), seleniumPath)

            olderThan27 = M.branch_compare(27, '<')

            if args.run:
                logging.info('Preparing Behat testing')

                # Preparing PHP Server
                phpServer = None
                if olderThan27 and not M.get('behat_switchcompletely'):
                    logging.info('Starting standalone PHP server')
                    kwargs = {}
                    kwargs['cwd'] = M.get('path')
                    phpServer = ProcessInThread(phpCommand, **kwargs)
                    phpServer.start()

                # Launching Selenium
                seleniumServer = None
                if seleniumPath and not nojavascript:
                    logging.info('Starting Selenium server')
                    kwargs = {}
                    if args.seleniumverbose:
                        kwargs['stdout'] = None
                        kwargs['stderr'] = None
                    seleniumServer = ProcessInThread(seleniumCommand, **kwargs)
                    seleniumServer.start()

                logging.info('Running Behat tests')

                # Sleep for a few seconds before starting Behat
                if phpServer or seleniumServer:
                    sleep(3)

                # Running the tests
                try:
                    process(cmd, M.path, None, None)
                except KeyboardInterrupt:
                    pass

                # Kill the remaining processes
                if phpServer and phpServer.is_alive():
                    phpServer.kill()
                if seleniumServer and seleniumServer.is_alive():
                    seleniumServer.kill()

                # Disable Behat
                if args.disable:
                    self.disable(M)

            else:
                if olderThan27:
                    logging.info('Launch PHP Server (or set $CFG->behat_switchcompletely to True):\n %s' % (phpCommand))
                if seleniumCommand:
                    logging.info('Launch Selenium (optional):\n %s' % (seleniumCommand))
                logging.info('Launch Behat:\n %s' % (cmd))

        except Exception as e:
            raise e

    def disable(self, M):
        logging.info('Disabling Behat')
        M.cli('admin/tool/behat/cli/util.php', '--disable')
        M.removeConfig('behat_switchcompletely')
