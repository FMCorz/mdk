"""
Moodle Development Kit

Copyright (c) 2025 Frédéric Massart

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

import argparse
from typing import List
from ..command import Command


class PhpCommand(Command):

    # We cannot define arguments, or they could conflict with the ones for PHP.
    _arguments = []
    _description = 'Invokes PHP in a Moodle instance'

    def parse_args(self, parser: argparse.ArgumentParser, sysargs: List[str]):
        [args, unknown] = parser.parse_known_args(sysargs)
        args.cmdargs = unknown
        return args

    def run(self, args):

        M = self.Wp.resolve(None)
        if not M:
            raise Exception('No instance to work on. Exiting...')

        M.php(args.cmdargs, stdout=None, stderr=None)
