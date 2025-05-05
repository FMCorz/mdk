#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Moodle Development Kit

Copyright (c) 2024 Frédéric Massart - FMCorz.net

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


class CronCommand(Command):

    _arguments = [
        (
            ['-k', '--keep-alive'],
            {
                'default': False,
                'help': 'keep alive the cron task',
                'dest': 'keepalive',
                'action': 'store_true'
            },
        ),
        (
            ['-t', '--task'],
            {
                'default': False,
                'help': 'the name of scheduled task to run, as component:taskname or component\\taskname',
                'dest': 'task',
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
    _description = 'Run cron'

    def run(self, args):

        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('No instance to work on. Exiting...')

        if args.task:
            taskname = args.task
            if ':' in args.task:
                parts = args.task.split(':')
                taskname = parts[0] + '\\task\\' + parts[1]
            elif '\\' in args.task and not '\\task\\' in args.task:
                parts = args.task.split('\\', 1)
                taskname = parts[0] + '\\task\\' + parts[1]

            logging.info('Executing task %s on %s' % (taskname, M.get('identifier')))
            r, _, _ = M.cli('admin/cli/scheduled_task.php', args=['--execute=%s' % taskname], stdout=None, stderr=None)

            if r > 0 and not taskname.endswith('_task'):
                taskname += '_task'
                logging.info('Retrying with %s' % (taskname))
                M.cli('admin/cli/scheduled_task.php', args=['--execute=%s' % taskname], stdout=None, stderr=None)

            return

        logging.info('Running cron on %s' % (M.get('identifier')))

        cliargs = []
        haskeepalive = M.branch_compare(401, '>')
        if not args.keepalive and haskeepalive:
            cliargs.append('--keep-alive=0')
        elif args.keepalive:
            if not haskeepalive:
                logging.warn('Option --keep-alive is not available for on older versions than 4.1')
            # Other versions keep-live by default, so no need for additional argument.

        M.cli('admin/cli/cron.php', args=cliargs, stdout=None, stderr=None)
