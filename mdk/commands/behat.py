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
from pathlib import Path
import urllib.request, urllib.parse, urllib.error
import re
import logging
import gzip
import json
from tempfile import gettempdir
from time import sleep
from ..command import Command
from ..tools import get_absolute_path, process, ProcessInThread, downloadProcessHook, question, natural_sort_key


class BehatCommand(Command):
    _arguments = [
        (
            ['-r', '--run'],
            {
                'action': 'store_true',
                'help': 'run the tests',
            },
        ),
        (
            ['-R', '--rerun'],
            {
                'action': 'store_true',
                'help': 're-run scenarios that failed during last execution, implies --run.',
            },
        ),
        (
            ['-d', '--disable'],
            {
                'action': 'store_true',
                'help': 'disable Behat, runs the tests first if --run has been set. Ignored from 2.7.',
                'silent': True,
            },
        ),
        (
            ['--force'],
            {
                'action': 'store_true',
                'help': 'force behat re-init and reset the variables in the config file.'
            },
        ),
        (
            ['-f', '--feature'],
            {
                'metavar': 'path',
                'help':
                    'typically a path to a feature, or an argument understood by behat (see [features]: '
                    'vendor/bin/behat --help). Automatically convert path to absolute path.'
            },
        ),
        (
            ['-n', '--testname'],
            {
                'dest': 'testname',
                'metavar': 'name',
                'help': 'only execute the feature elements which match part of the given name or regex'
            },
        ),
        (
            ['-p', '--profile'],
            {
                'metavar': 'profile',
                'help': 'the profile to use for running the tests, refers to $CFG->behat_profiles.'
            },
        ),
        (
            ['-t', '--tags'],
            {
                'metavar': 'tags',
                'help': 'only execute the features or scenarios with tags matching tag filter expression'
            },
        ),
        (
            ['-j', '--no-javascript'],
            {
                'action': 'store_true',
                'dest': 'nojavascript',
                'help':
                    'do not start Selenium and ignore Javascript (short for --tags=~@javascript). '
                    'Cannot be combined with --tags or --testname.'
            },
        ),
        (
            ['-D', '--no-dump'],
            {
                'action': 'store_false',
                'dest': 'faildump',
                'help': 'use the standard command without fancy screenshots or output to a directory'
            },
        ),
        (
            ['-k', '--skip-init'],
            {
                'action': 'store_true',
                'dest': 'skipinit',
                'help': 'allows tests to start quicker when the instance is already initialised'
            },
        ),
        (
            ['-S, --no-selenium'],
            {
                'action': 'store_true',
                'dest': 'noselenium',
                'help': 'when set, do not attempt to start Selenium',
            },
        ),
        (
            ['--selenium'],
            {
                'default': None,
                'dest': 'selenium',
                'help': 'path to the selenium standalone server to use',
                'metavar': 'jarfile'
            },
        ),
        (
            ['--selenium-download'],
            {
                'action': 'store_true',
                'dest': 'seleniumforcedl',
                'help': 'force the download of the latest Selenium to the cache'
            },
        ),
        (
            ['--selenium-verbose'],
            {
                'action': 'store_true',
                'dest': 'seleniumverbose',
                'help': 'outputs the output from selenium in the same window'
            },
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name',
                'nargs': '?'
            },
        ),
    ]
    _description = 'Initialise Behat'

    def run(self, args):
        withselenium = not (args.noselenium or args.nojavascript)
        shouldrun = args.run or args.rerun

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

        # Install Composer
        M.installComposerAndDevDependenciesIfNeeded()

        # Download selenium
        seleniumPath = None
        if withselenium:
            useSeleniumGrid = self.C.get('behat.useSeleniumGrid')
            seleniumFileName = 'selenium.jar'
            if useSeleniumGrid:
                seleniumFileName = 'selenium-grid.jar'
            seleniumPath = os.path.expanduser(os.path.join(self.C.get('dirs.mdk'), seleniumFileName))
            if args.selenium:
                seleniumPath = args.selenium
            elif args.seleniumforcedl or (not nojavascript and not os.path.isfile(seleniumPath)):
                if useSeleniumGrid:
                    self.handleDownloadSeleniumGrid(seleniumPath)
                else:
                    self.handleDownloadSeleniumLegacy(seleniumPath)

        if withselenium and not os.path.isfile(seleniumPath):
            raise Exception('Selenium file %s does not exist')

        # Run cli
        try:

            # If Oracle, ask the user for a Behat prefix, if not set.
            prefix = M.get('behat_prefix')
            if M.get('dbtype') == 'oci' and (args.force or not prefix or len(prefix) > 2):
                while not prefix or len(prefix) > 2:
                    prefix = question('What prefix would you like to use? (Oracle, max 2 chars)')
            else:
                prefix = None

            outputDir = (M.container.behat_faildumps or Path(self.Wp.getExtraDir(M.get('identifier'), 'behat'))).as_posix()
            outpurUrl = self.Wp.getUrl(M.get('identifier'), extra='behat')

            if not args.skipinit:
                logging.info('Initialising Behat, please be patient!')
                M.initBehat(force=args.force, prefix=prefix, faildumppath=outputDir)
                logging.info('Behat ready!')

            # Preparing Behat command
            cmd = ['vendor/bin/behat']
            if args.profile:
                cmd.append('--profile=%s' % (args.profile))

            if args.tags:
                cmd.append('--tags=%s' % (args.tags))

            if args.testname:
                cmd.append('--name=%s' % (args.testname))

            if not (args.tags or args.testname) and nojavascript:
                cmd.append('--tags ~@javascript')

            if args.rerun:
                cmd.append('--rerun')

            if args.faildump:
                if M.branch_compare(31, '<'):
                    cmd.append('--format="progress,progress,pretty,html,failed"')
                    cmd.append('--out=",{0}/progress.txt,{0}/pretty.txt,{0}/status.html,{0}/failed.txt"'.format(outputDir))
                else:
                    cmd.append('--format=moodle_progress')
                    cmd.append('--out=std')
                    cmd.append('--format=progress')
                    cmd.append('--out={0}/progress.txt'.format(outputDir))
                    cmd.append('--format=pretty')
                    cmd.append('--out={0}/pretty.txt'.format(outputDir))

            # Since Moodle 3.2.2 behat directory is kept under $CFG->behat_dataroot for single and parallel runs.
            configcandidates = ['%s/behatrun/behat/behat.yml' % M.container.behat_dataroot.as_posix()]
            if M.branch_compare(32, '<'):
                configcandidates.append('%s/behat/behat.yml' % M.container.behat_dataroot.as_posix())
            cmd.append('--config=%s' % (list(filter(lambda x: M.container.exists(Path(x)), configcandidates))[0]))

            # Checking feature argument. Assume either a path relative to the dirroot, or absolute within dirroot.
            if args.feature:
                featurepath = Path(args.feature).resolve()
                if featurepath.is_absolute() and not featurepath.exists():
                    featurepath = Path(M.get('path')) / Path(args.feature.lstrip('/'))
                cmd.append(featurepath.relative_to(Path(M.get('path'))).as_posix())

            seleniumCommand = None
            if seleniumPath:
                if self.C.get('behat.useSeleniumGrid'):
                    seleniumCommand = '%s -jar %s standalone' % (self.C.get('java'), seleniumPath)
                else:
                    seleniumCommand = '%s -jar %s' % (self.C.get('java'), seleniumPath)

            if shouldrun:
                logging.info('Preparing Behat testing')

                # Launching Selenium
                seleniumServer = None
                if seleniumPath and withselenium:
                    logging.info('Starting Selenium server')
                    kwargs = {}
                    if args.seleniumverbose:
                        kwargs['stdout'] = None
                        kwargs['stderr'] = None
                    else:
                        # Logging Selenium to a temporary file, this can be useful, and also it appears
                        # that Selenium hangs when stderr is not buffered.
                        fileOutPath = os.path.join(gettempdir(), 'selenium_%s_out.log' % (M.get('identifier')))
                        fileErrPath = os.path.join(gettempdir(), 'selenium_%s_err.log' % (M.get('identifier')))
                        tmpfileOut = open(fileOutPath, 'w')
                        tmpfileErr = open(fileErrPath, 'w')
                        logging.debug('Logging Selenium output to: %s' % (fileOutPath))
                        logging.debug('Logging Selenium errors to: %s' % (fileErrPath))
                        kwargs['stdout'] = tmpfileOut
                        kwargs['stderr'] = tmpfileErr
                    seleniumServer = ProcessInThread(seleniumCommand, **kwargs)
                    seleniumServer.start()

                logging.info('Running Behat tests')

                # Sleep for a few seconds before starting Behat
                if seleniumServer:
                    launchSleep = int(self.C.get('behat.launchSleep'))
                    logging.debug('Waiting for %d seconds to allow Selenium to start ' % (launchSleep))
                    sleep(launchSleep)

                # Running the tests
                try:
                    if args.faildump:
                        logging.info('More output can be found at:\n %s\n %s', outputDir, outpurUrl)
                    M.exec(cmd, stdout=None, stderr=None)
                except KeyboardInterrupt:
                    pass

                # Kill the remaining processes
                if seleniumServer and seleniumServer.is_alive():
                    seleniumServer.kill()

                # Disable Behat
                if args.disable:
                    self.disable(M)

            else:
                if args.faildump:
                    logging.info('More output will be accessible at:\n %s\n %s', outputDir, outpurUrl)
                if seleniumCommand:
                    logging.info('Launch Selenium (optional):\n %s' % (seleniumCommand))
                logging.info('Launch Behat:\n %s' % (' '.join(cmd)))

        except Exception as e:
            raise e

    def disable(self, M):
        logging.info('Disabling Behat')
        M.cli('admin/tool/behat/cli/util.php', ['--disable'])

    def handleDownloadSeleniumLegacy(self, seleniumPath):
        logging.info('Attempting to find a download for Selenium')
        seleniumStorageUrl = 'https://selenium-release.storage.googleapis.com/'
        url = urllib.request.urlopen(seleniumStorageUrl)
        content = url.read().decode('utf-8')
        matches = sorted(re.findall(r'[a-z0-9._-]+/selenium-server-standalone-[0-9.]+\.jar', content, re.I), key=natural_sort_key)
        if len(matches) > 0:
            seleniumUrl = seleniumStorageUrl + matches[-1]
            logging.info('Downloading Selenium from %s' % seleniumUrl)
            self.downloadSelenium(seleniumUrl, seleniumPath)
        else:
            logging.warning('Could not locate Selenium server to download')

    def handleDownloadSeleniumGrid(self, seleniumPath):
        logging.info('Attempting to find a download for Selenium Grid')
        seleniumStorageUrl = 'https://api.github.com/repos/SeleniumHQ/selenium/releases/latest'
        url = urllib.request.urlopen(seleniumStorageUrl)
        content = json.load(url)
        if 'assets' in content:
            assets = content['assets']
            matches = []
            for asset in assets:
                if re.search(r'selenium-server-[0-9.]+\.jar', asset['name']):
                    matches.append(asset['browser_download_url'])
            if len(matches) > 0:
                seleniumUrl = matches[-1]
                logging.info('Downloading Selenium Grid from %s' % seleniumUrl)
                self.downloadSelenium(seleniumUrl, seleniumPath)
            else:
                logging.warning('Could not locate Selenium Grid to download')
        else:
            logging.warning('Could not locate Selenium Grid to download')

    def downloadSelenium(self, seleniumUrl, seleniumPath):
        if (logging.getLogger().level <= logging.INFO):
            urllib.request.urlretrieve(seleniumUrl, seleniumPath, downloadProcessHook)
            # Force a new line after the hook display
            logging.info('')
        else:
            urllib.request.urlretrieve(seleniumUrl, seleniumPath)
