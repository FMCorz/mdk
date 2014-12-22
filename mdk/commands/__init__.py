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


def getCommand(cmd):
    """Lazy loading of a command class. Millseconds saved, hurray!"""
    cls = cmd.capitalize() + 'Command'
    return getattr(getattr(getattr(__import__('mdk.%s.%s' % ('commands', cmd)), 'commands'), cmd), cls)

commandsList = [
    'alias',
    'backport',
    'backup',
    'behat',
    'config',
    'create',
    'css',
    'doctor',
    'fix',
    'info',
    'init',
    'install',
    'js',
    'phpunit',
    'plugin',
    'precheck',
    'pull',
    'purge',
    'push',
    'rebase',
    'remove',
    'run',
    'tracker',
    'uninstall',
    'update',
    'upgrade'
]
