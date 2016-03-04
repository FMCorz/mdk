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
import time
import watchdog.events
import watchdog.observers
from .. import css
from ..command import Command


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
            ['-s', '--sheets'],
            {
                'action': 'store',
                'dest': 'sheets',
                'default': None,
                'help': 'the sheets to work on without their extensions. When not specified, it is guessed from the less folder.',
                'nargs': '+'
            }
        ),
        (
            ['-t', '--theme'],
            {
                'action': 'store',
                'dest': 'theme',
                'default': None,
                'help': 'the theme to work on. The default is \'bootstrapbase\' but is ignored if we are in a theme folder.',
            }
        ),
        (
            ['-d', '--debug'],
            {
                'action': 'store_true',
                'dest': 'debug',
                'help': 'produce an unminified debugging version with source maps'
            }
        ),
        (
            ['-w', '--watch'],
            {
                'action': 'store_true',
                'dest': 'watch',
                'help': 'watch the directory'
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

        # Resolve the theme folder we are in.
        if not args.theme:
            mpath = os.path.join(Mlist[0].get('path'), 'theme')
            cwd = os.path.realpath(os.path.abspath(os.getcwd()))
            if cwd.startswith(mpath):
                candidate = cwd.replace(mpath, '').strip('/')
                while True:
                    (head, tail) = os.path.split(candidate)
                    if not head and tail:
                        # Found the theme.
                        args.theme = tail
                        logging.info('You are in the theme \'%s\', using that.' % (args.theme))
                        break
                    elif not head and not tail:
                        # Nothing, let's leave.
                        break
                    candidate = head

        # We have not found anything, falling back on the default.
        if not args.theme:
            args.theme = 'bootstrapbase'

        for M in Mlist:
            if args.compile:
                logging.info('Compiling theme \'%s\' on %s' % (args.theme, M.get('identifier')))
                processor = css.Css(M)
                processor.setDebug(args.debug)
                if args.debug:
                    processor.setCompiler('lessc')
                elif M.branch_compare(29, '<'):
                    # Grunt was only introduced for 2.9.
                    processor.setCompiler('recess')

                processor.compile(theme=args.theme, sheets=args.sheets)

        # Setting up watchdog. This code should be improved when we will have more than a compile option.
        observer = None
        if args.compile and args.watch:
            observer = watchdog.observers.Observer()

        for M in Mlist:
            if args.watch and args.compile:
                processor = css.Css(M)
                processorArgs = {'theme': args.theme, 'sheets': args.sheets}
                handler = LessWatcher(M, processor, processorArgs)
                observer.schedule(handler, processor.getThemeLessPath(args.theme), recursive=True)
                logging.info('Watchdog set up on %s/%s, waiting for changes...' % (M.get('identifier'), args.theme))

        if observer and args.compile and args.watch:
            observer.start()

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            finally:
                observer.join()


class LessWatcher(watchdog.events.FileSystemEventHandler):

    _processor = None
    _args = None
    _ext = '.less'
    _M = None

    def __init__(self, M, processor, args):
        super(self.__class__, self).__init__()
        self._M = M
        self._processor = processor
        self._args = args

    def on_modified(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event):
        if event.is_directory:
            return
        elif not event.src_path.endswith(self._ext):
            return

        filename = event.src_path.replace(self._processor.getThemeLessPath(self._args['theme']), '').strip('/')
        logging.info('[%s] Changes detected in %s!' % (self._M.get('identifier'), filename))
        self._processor.compile(**self._args)
