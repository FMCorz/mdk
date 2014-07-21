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
from lib import tools, jira
from lib.command import Command
from lib.tools import question

class ResetCommand(Command):

    _arguments = [
    ]
    _description = 'Reset back to the main branch for this installation'

    def run(self, args):

        M = self.Wp.resolve()
        if not M:
            raise Exception('This is not a Moodle instance')

        # Reading the information about the current instance.
        branch = M.get('stablebranch')

        if not M.git().checkout(branch):
            raise Exception('Could not checkout branch %s' % (branch))
        logging.info('Checked out branch %s' % (branch))
