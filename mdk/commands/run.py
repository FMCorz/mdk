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
from ..command import Command
from ..scripts import Scripts


class RunCommand(Command):

    _arguments = [
        (
            ['-l', '--list'],
            {
                'action': 'store_true',
                'dest': 'list',
                'help': 'list the available scripts'
            }
        ),
        (
            ['-a', '--all'],
            {
                'action': 'store_true',
                'dest': 'all',
                'help': 'runs the script on each instance'
            }
        ),
        (
            ['-i', '--integration'],
            {
                'action': 'store_true',
                'dest': 'integration',
                'help': 'runs the script on integration instances'
            }
        ),
        (
            ['-s', '--stable'],
            {
                'action': 'store_true',
                'dest': 'stable',
                'help': 'runs the script on stable instances'
            }
        ),
        (
            ['-g', '--arguments'],
            {
                'help': 'a list of arguments to pass to the script. Use --arguments="--list of --arguments" if you need to use dashes. Otherwise add -- after the argument list.',
                'metavar': 'arguments',
                'nargs': '+'
            }
        ),
        (
            ['script'],
            {
                'nargs': '?',
                'help': 'the name of the script to run'
            }
        ),
        (
            ['names'], {
                'default': None,
                'help': 'name of the instances',
                'nargs': '*'
            }
        )
    ]
    _description = 'Run a script on a Moodle instance'

    def run(self, args):

        # Printing existing scripts
        if args.list:
            scripts = Scripts.list()
            for script in sorted(scripts.keys()):
                print u'%s (%s)' % (script, scripts[script])
            return

        # Trigger error when script is missing
        if not args.script:
            self.argumentError('missing script name')

        # Resolving instances
        names = args.names
        if args.all:
            names = self.Wp.list()
        elif args.integration or args.stable:
            names = self.Wp.list(integration=args.integration, stable=args.stable)

        # Doing stuff
        Mlist = self.Wp.resolveMultiple(names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        for M in Mlist:
            logging.info('Running \'%s\' on \'%s\'' % (args.script, M.get('identifier')))
            try:
                M.runScript(args.script, stderr=None, stdout=None, arguments=args.arguments)
            except Exception as e:
                logging.warning('Error while running the script on %s' % M.get('identifier'))
                logging.debug(e)
            else:
                logging.info('')

        logging.info('Done.')
