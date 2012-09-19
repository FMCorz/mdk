#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2012 Frédéric Massart - FMCorz.net

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

import sys
import argparse
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description='Purge an instance cache')
parser.add_argument('-a', '--all', action='store_true', help='runs the script on every instances', dest='all')
parser.add_argument('-i', '--integration', action='store_true', help='runs the script on the integration instances', dest='integration')
parser.add_argument('-s', '--stable', action='store_true', help='runs the script on the stable instances', dest='stable')
parser.add_argument('names', metavar='names', default=None, nargs='*', help='name of the instances')
args = parser.parse_args()

# Resolving instances
names = args.names
if args.all:
    names = Wp.list()
elif args.integration or args.stable:
    names = Wp.list(integration = args.integration, stable = args.stable)

# Doing stuff
Mlist = Wp.resolveMultiple(names)
if len(Mlist) < 1:
    debug('No instances to work on. Exiting...')
    sys.exit(1)

for M in Mlist:
    debug('Purging cache on %s' % (M.get('identifier')))

    if not M.isInstalled():
        debug('Instance not installed. Skipping...')
        debug('')
        continue
    elif M.branch_compare('22', '<'):
        debug('Instance does not support cache purging. Skipping...')
        debug('')
        continue

    try:
    	M.cli('admin/cli/purge_caches.php', stderr=None, stdout=None)
    except Exception as e:
        debug('Error while purging cache!')
    else:
        debug('Cache purged!')

    debug('')

debug('Done.')
