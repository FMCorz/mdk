#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from lib import moodle, workplace, config
from lib.tools import debug

# Arguments
parser = argparse.ArgumentParser(description='Initialize PHP Unit')
parser.add_argument('name', metavar='name', default=None, nargs='?', help='name of the instance')
args = parser.parse_args()

C = config.Conf().get

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

# Check if installed
if not M.get('installed'):
    debug('This instance needs to be installed first')
    sys.exit(1)

# Run cli
try:
    M.initPHPUnit()
    debug('PHP Unit ready!')
except Exception as e:
    debug(e)
    sys.exit(1)
