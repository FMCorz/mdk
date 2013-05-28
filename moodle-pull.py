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

import sys
from os.path import basename
from lib.command import CommandRunner
from lib.commands import getCommand
from lib.config import Conf

f = basename(__file__)
sys.stderr.write("Do not call %s directly.\n" % (f))
sys.stderr.write("This file will be removed in a later version.\n")
sys.stderr.write("Please use `mdk [command] [arguments]`\n")
sys.stderr.write("\n")

cmd = f.replace('moodle-', '').replace('.py', '')
cls = getCommand(cmd)
Cmd = cls(Conf())
Runner = CommandRunner(Cmd)
Runner.run(None, prog='%s %s' % ('mdk', cmd))
