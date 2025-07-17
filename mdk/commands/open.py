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

import logging

from mdk.tools import open_in_browser

from ..command import Command

logger = logging.getLogger(__name__)


class OpenCommand(Command):

    _description = "Opens an instance in the browser"

    def setup_args(self, parser):
        parser.add_argument('instance', nargs='?', help='name of the instance')

    def run(self, args):
        M = self.Wp.resolve(args.instance, raise_exception=True)
        if not M.isInstalled():
            raise Exception(f'Moodle instance {M.get("identifier")} is not installed.')
        wwwroot = M.get('wwwroot')
        open_in_browser(wwwroot)
