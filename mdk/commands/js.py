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
import datetime
import watchdog.events
import watchdog.observers
from ..command import Command
from .. import js, plugins


class JsCommand(Command):

    _arguments = [
        (
            ['mode'],
            {
                'metavar': 'mode',
                'help': 'the type of action to perform',
                'sub-commands':
                    {
                        'shift': (
                            {
                                'help': 'keen to use shifter?'
                            },
                            [
                                (
                                    ['-p', '--plugin'],
                                    {
                                        'action': 'store',
                                        'dest': 'plugin',
                                        'default': None,
                                        'help': 'the name of the plugin or subsystem to target. If not passed, we do our best to guess from the current path.'
                                    }
                                ),
                                (
                                    ['-m', '--module'],
                                    {
                                        'action': 'store',
                                        'dest': 'module',
                                        'default': None,
                                        'help': 'the name of the module in the plugin or subsystem. If omitted all the modules will be shifted, except we are in a module.'
                                    }
                                ),
                                (
                                    ['-w', '--watch'],
                                    {
                                        'action': 'store_true',
                                        'dest': 'watch',
                                        'help': 'watch for changes to re-shift'
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
                        ),
                        'doc': (
                            {
                                'help': 'keen to generate documentation?'
                            },
                            [
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
                        )
                    }
            }
        )
    ]
    _description = 'Wrapper for JS functions'

    def run(self, args):
        if args.mode == 'shift':
            self.shift(args)
        elif args.mode == 'doc':
            self.document(args)


    def shift(self, args):
        """The shift mode"""

        Mlist = self.Wp.resolveMultiple(args.names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        cwd = os.path.realpath(os.path.abspath(os.getcwd()))
        mpath = Mlist[0].get('path')
        relpath = cwd.replace(mpath, '').strip('/')

        # TODO Put that logic somewhere else because it is going to be re-used, I'm sure.
        if not args.plugin:
            (subsystemOrPlugin, pluginName) = plugins.PluginManager.getSubsystemOrPluginFromPath(cwd, Mlist[0])
            if subsystemOrPlugin:
                args.plugin = subsystemOrPlugin + ('_' + pluginName) if pluginName else ''
                logging.info("I guessed the plugin/subsystem to work on as '%s'" % (args.plugin))
            else:
                self.argumentError('The argument --plugin is required, I could not guess it.')

        if not args.module:
            candidate = relpath
            module = None
            while '/yui/src' in candidate:
                (head, tail) = os.path.split(candidate)
                if head.endswith('/yui/src'):
                    module = tail
                    break
                candidate = head

            if module:
                args.module = module
                logging.info("I guessed the JS module to work on as '%s'" % (args.module))

        for M in Mlist:
            if len(Mlist) > 1:
                logging.info('Let\'s shift everything you wanted on \'%s\'' % (M.get('identifier')))

            processor = js.Js(M)
            processor.shift(subsystemOrPlugin=args.plugin, module=args.module)

        if args.watch:
            observer = watchdog.observers.Observer()

            for M in Mlist:
                processor = js.Js(M)
                processorArgs = {'subsystemOrPlugin': args.plugin, 'module': args.module}
                handler = JsShiftWatcher(M, processor, processorArgs)
                observer.schedule(handler, processor.getYUISrcPath(**processorArgs), recursive=True)
                logging.info('Watchdog set up on %s, waiting for changes...' % (M.get('identifier')))

            observer.start()

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            finally:
                observer.join()

    def document(self, args):
        """The docmentation mode"""

        Mlist = self.Wp.resolveMultiple(args.names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        for M in Mlist:
            logging.info('Documenting everything you wanted on \'%s\'. This may take a while...', M.get('identifier'))
            outdir = self.Wp.getExtraDir(M.get('identifier'), 'jsdoc')
            outurl = self.Wp.getUrl(M.get('identifier'), extra='jsdoc')
            processor = js.Js(M)
            processor.document(outdir)
            logging.info('Documentation available at:\n %s\n %s', outdir, outurl)


class JsShiftWatcher(watchdog.events.FileSystemEventHandler):

    _processor = None
    _args = None
    _ext = ['.js', '.json']
    _M = None

    def __init__(self, M, processor, args):
        super(self.__class__, self).__init__()
        self._M = M
        self._processor = processor
        self._args = args

    def on_modified(self, event):
        if event.is_directory:
            return
        elif not os.path.splitext(event.src_path)[1] in self._ext:
            return
        self.process(event)

    def on_moved(self, event):
        if not os.path.splitext(event.dest_path)[1] in self._ext:
            return
        self.process(event)

    def process(self, event):
        logging.info('[%s] (%s) Changes detected!' % (self._M.get('identifier'), datetime.datetime.now().strftime('%H:%M:%S')))

        try:
            self._processor.shift(**self._args)
        except js.ShifterCompileFailed:
            logging.error(' /!\ Error: Compile failed!')
