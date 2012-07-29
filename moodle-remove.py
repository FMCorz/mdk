#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

from lib import config, tools, workplace
from lib.tools import debug

C = config.Conf().get

# Arguments
parser = argparse.ArgumentParser(description='Completely remove an instance')
parser.add_argument('name', help='name of the instance')
parser.add_argument('-y', action='store_true', help='do not ask for confirmation', dest='do')
args = parser.parse_args()

Wp = workplace.Workplace()
try:
	M = Wp.get(args.name)
except:
	debug('This is not a Moodle instance')
	sys.exit(1)

if not args.do:
	confirm = raw_input('Are you sure? (Y/n) ')
	if confirm != 'Y':
		debug('Exiting...')
		sys.exit(0)

debug('Removing %s...' % args.name)
Wp.delete(args.name)
debug('Instance removed')
