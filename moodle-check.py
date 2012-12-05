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
import os
import argparse
from lib import workplace
from lib.tools import debug
from lib.config import Conf

Wp = workplace.Workplace()
C = Conf()

# Arguments
parser = argparse.ArgumentParser(description='Perform several checks on your current installation')
# parser.add_argument('-f', '--fix', dest='fix', action='store_true', help='Fix the problems where possible')
parser.add_argument('-i', '--integration', action='store_true', help='runs the script on the integration instances', dest='integration')
parser.add_argument('-s', '--stable', action='store_true', help='runs the script on the stable instances', dest='stable')
parser.add_argument('names', metavar='names', default=None, nargs='*', help='name of the instances')
args = parser.parse_args()

# Check configuration file
debug('[Config file]')
distSettings = Conf(os.path.dirname(__file__), 'config-dist.json').get()
allSettings = C.get()

errors = []
def dictCompare(orig, mine, path = ''):
    for k in orig:
        currentpath = path + '.' + k
        currentpath = currentpath.strip('.')
        if k not in mine:
            errors.append(currentpath)
        elif type(orig[k]) in (dict, list):
            dictCompare(orig[k], mine[k], currentpath)
dictCompare(distSettings, allSettings)

if len(errors) > 0:
    for err in errors:
        debug(u'Missing setting %s' % err)
else:
    debug('All good!')
debug('')

# Checking instances
names = args.names
if not names:
    names = Wp.list()
elif args.integration or args.stable:
    names = Wp.list(integration = args.integration, stable = args.stable)

Mlist = Wp.resolveMultiple(names)
if len(Mlist) < 1:
    debug('No instances to check.')
else:
    upstream = C.get('upstreamRemote')
    myremote = C.get('myRemote')
    myremoteurl = C.get('remotes.mine')

    if C.get('useCacheAsRemote'):
        remoteInt = os.path.abspath(os.path.realpath(os.path.join(C.get('dirs.mdk'), 'integration.git')))
        remoteSta = os.path.abspath(os.path.realpath(os.path.join(C.get('dirs.mdk'), 'moodle.git')))
    else:
        remoteInt = C.get('remotes.integration')
        remoteSta = C.get('remotes.stable')

    for M in Mlist:
        errors = []
        isIntegration = M.isIntegration()

        # Checking remotes
        if upstream:
            thisupstream = M.git().getRemote(upstream)
            if not thisupstream:
                errors.append('Missing remote %s' % upstream)
            elif isIntegration and thisupstream != remoteInt:
                errors.append('Remote %s is not %s' % (upstream, remoteInt))
            elif not isIntegration and thisupstream != remoteSta:
                errors.append('Remote %s is not %s' % (upstream, remoteSta))

        if myremote:
            thismyremote = M.git().getRemote(myremote)
            if not thismyremote:
                errors.append('Missing remote %s' % myremote)
            elif thismyremote != myremoteurl:
                errors.append('Remote %s is not %s' % (myremote, myremoteurl))

        if len(errors) > 0:
            debug('[%s]' % M.get('identifier'))
            for err in errors:
                debug(u'  %s' % err)

# Done.
debug('')
debug('Done.')
