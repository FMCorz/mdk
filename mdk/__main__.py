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

def main():

    import sys
    import argparse
    import os
    import re
    import logging
    from .command import CommandRunner
    from .commands import getCommand, commandsList
    from .config import Conf
    from .tools import process
    from .version import __version__

    C = Conf()

    try:
        debuglevel = getattr(logging, C.get('debug').upper())
    except AttributeError:
        debuglevel = logging.INFO

    # Set logging levels.
    logging.basicConfig(format='%(message)s', level=debuglevel)
    logging.getLogger('requests').setLevel(logging.WARNING)  # Reset logging level of 'requests' module.

    availaliases = [str(x) for x in C.get('aliases').keys()]
    choices = sorted(commandsList + availaliases)

    parser = argparse.ArgumentParser(description='Moodle Development Kit', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', help='show this help message and exit')
    parser.add_argument('-l', '--list', action='store_true', help='list the available commands')
    parser.add_argument('-v', '--version', action='store_true', help='display the current version')
    parser.add_argument(*['--%s'%f.decode('base64') for f in ('aWNhbnRyZWFj', 'aWNhbnRyZWFk')], dest='asdf', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('command', metavar='command', nargs='?', help='command to call', choices=choices)
    parser.add_argument('args', metavar='arguments', nargs=argparse.REMAINDER, help='arguments of the command')
    parsedargs = parser.parse_args()

    cmd = parsedargs.command
    args = parsedargs.args

    # There is no command, what do we do?
    if not cmd:
        if parsedargs.version:
            print 'MDK version %s' % __version__
        elif parsedargs.asdf:
            print 'U29ycnkgRGF2ZSwgTURLIGNhbm5vdCBoZWxwIHlvdSB3aXRoIHRoYXQuLi4='.decode('base64')
        elif parsedargs.list:
            for c in sorted(commandsList):
                print '{0:<15} {1}'.format(c, getCommand(c)._description)
        else:
            parser.print_help()
        sys.exit(0)

    # Looking up for an alias
    alias = C.get('aliases.%s' % cmd)
    if alias != None:
        if alias.startswith('!'):
            cmd = alias[1:]
            i = 0
            # Replace $1, $2, ... with passed arguments
            for arg in args:
                i += 1
                cmd = cmd.replace('$%d' % i, arg)
            # Remove unknown $[0-9]
            cmd = re.sub(r'\$[0-9]', '', cmd)
            result = process(cmd, stdout=None, stderr=None)
            sys.exit(result[0])
        else:
            cmd = alias.split(' ')[0]
            args = alias.split(' ')[1:] + args

    cls = getCommand(cmd)
    Cmd = cls(C)
    Runner = CommandRunner(Cmd)
    try:
        Runner.run(args, prog='%s %s' % (os.path.basename(sys.argv[0]), cmd))
    except Exception as e:
        import traceback
        info = sys.exc_info()
        logging.error('%s: %s', e.__class__.__name__, e)
        logging.debug(''.join(traceback.format_tb(info[2])))
        sys.exit(1)

if __name__ == "__main__":
    main()
