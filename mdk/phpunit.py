#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2014 Frédéric Massart - FMCorz.net

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
from .config import Conf
from .tools import mkdir, process

C = Conf()


class PHPUnit(object):
    """Class wrapping PHPUnit functions"""

    _M = None
    _Wp = None

    def __init__(self, Wp, M):
        self._Wp = Wp
        self._M = M

    def getCommand(self, testcase=None, unittest=None, filter=None, coverage=None, testsuite=None, stopon=None):
        """Get the PHPUnit command"""
        cmd = []
        if self.usesComposer():
            cmd.append('vendor/bin/phpunit')
        else:
            cmd.append('phpunit')

        if coverage:
            cmd.append('--coverage-html')
            cmd.append(self.getCoverageDir())

        if stopon:
            for on in stopon:
                cmd.append('--stop-on-%s' % on)

        if testcase:
            cmd.append(testcase)
        elif unittest:
            cmd.append(unittest)
        elif filter:
            cmd.append('--filter="%s"' % filter)
        elif testsuite:
            cmd.append('--testsuite')
            cmd.append(testsuite)

        return cmd

    def getCoverageDir(self):
        """Get the Coverage directory, and create it if required"""
        return self.Wp.getExtraDir(self.M.get('identifier'), 'coverage')

    def getCoverageUrl(self):
        """Return the code coverage URL"""
        return self.Wp.getUrl(self.M.get('identifier'), extra='coverage')

    def init(self, force=False, prefix=None):
        """Initialise the PHPUnit environment"""

        if self.M.branch_compare(23, '<'):
            raise Exception('PHPUnit is only available from Moodle 2.3')

        # Set PHPUnit data root
        phpunit_dataroot = self.M.get('dataroot') + '_phpu'
        self.M.updateConfig('phpunit_dataroot', phpunit_dataroot)
        if not os.path.isdir(phpunit_dataroot):
            mkdir(phpunit_dataroot, 0777)

        # Set PHPUnit prefix
        currentPrefix = self.M.get('phpunit_prefix')
        phpunit_prefix = prefix or 'phpu_'

        if not currentPrefix or force:
            self.M.updateConfig('phpunit_prefix', phpunit_prefix)
        elif currentPrefix != phpunit_prefix and self.M.get('dbtype') != 'oci':
            # Warn that a prefix is already set and we did not change it.
            # No warning for Oracle as we need to set it to something else.
            logging.warning('PHPUnit prefix not changed, already set to \'%s\', expected \'%s\'.' % (currentPrefix, phpunit_prefix))

        result = (None, None, None)
        exception = None
        try:
            if force:
                result = self.M.cli('/admin/tool/phpunit/cli/util.php', args='--drop', stdout=None, stderr=None)
            result = self.M.cli('/admin/tool/phpunit/cli/init.php', stdout=None, stderr=None)
        except Exception as exception:
            pass

        if exception != None or result[0] > 0:
            if result[0] == 129:
                raise Exception('PHPUnit is not installed on your system')
            elif result[0] > 0:
                raise Exception('Something wrong with PHPUnit configuration')
            else:
                raise exception

        logging.info('PHPUnit ready!')

    def run(self, **kwargs):
        """Execute the command"""
        cmd = self.getCommand(**kwargs)
        return process(cmd, self.M.get('path'), None, None)

    def usesComposer(self):
        """Return whether or not the instance uses composer, the latter is considered installed"""
        return os.path.isfile(os.path.join(self.M.get('path'), 'composer.json'))

    @property
    def M(self):
        return self._M

    @property
    def Wp(self):
        return self._Wp
