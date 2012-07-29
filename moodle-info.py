#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
from lib import config, workplace, moodle, tools
from lib.tools import debug

C = config.Conf().get

# Arguments
parser = argparse.ArgumentParser(description='Shows information about a Moodle instance')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

# Loading instance
try:
	if args.name != None:
		Wp = workplace.Workplace()
		M = Wp.get(args.name)
	else:
		M = moodle.Moodle(os.getcwd())
		if not M:
			raise Exception()
except Exception:
	debug('This is not a Moodle instance')
	sys.exit(1)

# Printing info
for key, info in M.info().items():
	print '%s: %s' % (key, info)
