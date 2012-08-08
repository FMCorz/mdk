#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get
Wp = workplace.Workplace()

# Arguments
parser = argparse.ArgumentParser(description='Runs the Moodle upgrade script')
parser.add_argument('-a', '--all', action='store_true', help='runs the script on every instances', dest='all')
parser.add_argument('-i', '--integration', action='store_true', help='runs the script on the integration instances', dest='integration')
parser.add_argument('-s', '--stable', action='store_true', help='runs the script on the stable instances', dest='stable')
parser.add_argument('-u', '--update', action='store_true', help='update the instance before running the upgrade script', dest='update')
parser.add_argument('names', metavar='names', default=None, nargs='*', help='name of the instances')
args = parser.parse_args()

names = args.names
if args.all:
	names = Wp.list()
elif args.integration or args.stable:
	names = Wp.list(integration = args.integration, stable = args.stable)

Mlist = Wp.resolveMultiple(names)
if len(Mlist) < 1:
    debug('No instances to work on. Exiting...')
    sys.exit(1)

for M in Mlist:
	if args.update:
		debug('Updating %s...' % M.get('identifier'))
		M.update()
	debug('Upgrading %s...' % M.get('identifier'))
	if M.upgrade():
		debug('Error during the upgrade of %s' % M.get('identifier'))
	debug('')

debug('Done.')
