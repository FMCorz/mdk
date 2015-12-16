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

import logging
import os
import gzip
import urllib
from ..command import Command
from ..tools import process, question
from ..phpunit import PHPUnit


class PhpunitCommand(Command):

    _arguments = [
        (
            ['-f', '--force'],
            {
                'action': 'store_true',
                'help': 'force the initialisation'
            }
        ),
        (
            ['-r', '--run'],
            {
                'action': 'store_true',
                'help': 'also run the tests'
            }
        ),
        (
            ['-t', '--testcase'],
            {
                'default': None,
                'help': 'testcase class to run (From Moodle 2.6)',
                'metavar': 'testcase'
            }
        ),
        (
            ['-s', '--testsuite'],
            {
                'default': None,
                'help': 'testsuite to run',
                'metavar': 'testsuite'
            }
        ),
        (
            ['-u', '--unittest'],
            {
                'default': None,
                'help': 'test file to run',
                'metavar': 'path'
            }
        ),
        (
            ['-k', '--skip-init'],
            {
                'action': 'store_true',
                'dest': 'skipinit',
                'help': 'allows tests to start quicker when the instance is already initialised'
            }
        ),
        (
            ['-q', '--stop-on-failure'],
            {
                'action': 'store_true',
                'dest': 'stoponfailure',
                'help': 'stop execution upon first failure or error'
            }
        ),
        (
            ['-c', '--coverage'],
            {
                'action': 'store_true',
                'help': 'creates the HTML code coverage report'
            }
        ),
        (
            ['--filter'],
            {
                'default': None,
                'help': 'filter to pass through to PHPUnit',
                'metavar': 'filter'
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
    _description = 'Initialize PHPUnit'

    def run(self, args):

        # Loading instance
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        # Check if installed
        if not M.get('installed'):
            raise Exception('This instance needs to be installed first')

        # Check if testcase option is available.
        if args.testcase and M.branch_compare('26', '<'):
            self.argumentError('The --testcase option only works with Moodle 2.6 or greater.')

        # Create the Unit test object.
        PU = PHPUnit(self.Wp, M)

        # Skip init.
        if not args.skipinit:
            self.init(M, PU, args)

        # Automatically add the suffix _testsuite.
        testsuite = args.testsuite
        if testsuite and not testsuite.endswith('_testsuite'):
            testsuite += '_testsuite'

        kwargs = {
            'coverage': args.coverage,
            'filter': args.filter,
            'testcase': args.testcase,
            'testsuite': testsuite,
            'unittest': args.unittest,
            'stopon': [] if not args.stoponfailure else ['failure']
        }

        if args.run:
            PU.run(**kwargs)
            if args.coverage:
                logging.info('Code coverage is available at: \n %s', (PU.getCoverageUrl()))
        else:
            logging.info('Start PHPUnit:\n %s', (' '.join(PU.getCommand(**kwargs))))

    def init(self, M, PU, args):
        """Initialises PHP Unit"""

        # Install Composer
        if PU.usesComposer():
            if not os.path.isfile(os.path.join(M.get('path'), 'composer.phar')):
                logging.info('Installing Composer')
                cliFile = 'phpunit_install_composer.php'
                cliPath = os.path.join(M.get('path'), 'phpunit_install_composer.php')
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

        # If Oracle, ask the user for a Behat prefix, if not set.
        prefix = M.get('phpunit_prefix')
        if M.get('dbtype') == 'oci' and (args.force or not prefix or len(prefix) > 2):
            while not prefix or len(prefix) > 2:
                prefix = question('What prefix would you like to use? (Oracle, max 2 chars)')
        else:
            prefix = None

        PU.init(force=args.force, prefix=prefix)


