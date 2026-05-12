#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Moodle Development Kit

Copyright (c) 2026 Frédéric Massart - FMCorz.net

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
from pathlib import Path
import sys

from mdk.tools import get_absolute_path

from ..command import Command, CommandArgumentError, CommandArgumentParser
from ..paths import ComponentResolver, get_file_path_from_classname

logger = logging.getLogger(__name__)


class PathCommand(Command):

    _arguments = []
    _description = 'Resolve paths to and within a Moodle instance'

    def setup_args(self, parser: CommandArgumentParser) -> None:
        parser.add_argument(
            '--class',
            dest='classname',
            default=None,
            metavar='classname',
            help='resolves a PHP class to a file path, prioritising existing classes',
        )
        parser.add_argument(
            '--component',
            default=None,
            metavar='name',
            help='component or plugin name (frankenstyle), plugintype, or subsystem',
        )
        parser.add_argument(
            '--container',
            action='store_true',
            dest='container',
            help='resolves the absolute path inside the resolved container',
        )
        parser.add_argument(
            '--exists',
            action='store_true',
            dest='exists',
            help='exit with an error if the resolved path does not exist',
        )
        parser.add_argument(
            '--relative',
            action='store_true',
            dest='relative',
            help='return the path as a relative path to the root directory',
        )
        parser.add_argument(
            '--subpath',
            default=None,
            metavar='path',
            help='append a relative path, automatically handles public/ prefix, relative to --component if provided',
        )
        parser.add_argument(
            'name',
            nargs='?',
            default=None,
            metavar='name',
            help='name of the Moodle instance',
        )

    def run(self, args):
        if args.classname and bool(args.component or args.subpath):
            raise CommandArgumentError('The argument --class cannot be used with --component or --subpath')

        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        dirroot = Path(M.path).resolve()
        admin = M.get('admin', 'admin') or 'admin'
        resolver = ComponentResolver(dirroot, admin=admin)

        path = dirroot
        if args.component:
            path = resolver.get_component_directory(args.component)

        if args.subpath:
            path = path / args.subpath.relative_to('/')

        if args.classname:
            path = get_file_path_from_classname(args.classname, resolver)

        if not path:
            logging.error('Could not resolve path')
            sys.exit(1)

        abspath = path.resolve()
        if args.exists and not abspath.exists():
            logging.error('Path does not exist: %s', abspath)
            sys.exit(1)

        relpath = abspath.relative_to(dirroot)
        if args.container:
            abspath = get_absolute_path(relpath, M.container.path)

        print(abspath if not args.relative else relpath)
