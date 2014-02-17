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
from lib.command import Command
from lib import css


class CssCommand(Command):

    _arguments = [
        (
            ['-c', '--compile'],
            {
                'action': 'store_true',
                'dest': 'compile',
                'help': 'compile the theme less files'
            }
        ),
        (
            ['names'],
            {
                'default': None,
                'help': 'name of the instances',
                'metavar': 'names',
                'nargs': '*'
            }
        )
    ]
    _description = 'Wrapper for CSS functions'

    def run(self, args):

        Mlist = self.Wp.resolveMultiple(args.names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        for M in Mlist:
            if args.compile:
                processor = css.Css(M)
                processor.compile()
