#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import subprocess
from lib import moodle, workplace, config
from lib.tools import debug

# Arguments
parser = argparse.ArgumentParser(description='Initialize PHP Unit')
parser.add_argument('-n', '--name', metavar='name', default=None, help='name of the instance')
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

# Set PHP Unit data root
phpunit_dataroot = M.get('dataroot') + '_phpu'
if M.get('phpunit_dataroot') == None:
    M.addConfig('phpunit_dataroot', phpunit_dataroot)
elif M.get('phpunit_dataroot') != phpunit_dataroot:
    debug('Excepted value for phpunit_dataroot is \'%s\'. Please manually fix.' % phpunit_dataroot)
    sys.exit(1)
if not os.path.isdir(phpunit_dataroot):
    os.mkdir(phpunit_dataroot, 0777)

# Set PHP Unit prefix
phpunit_prefix = 'php_u'
if M.get('phpunit_prefix') == None:
    M.addConfig('phpunit_prefix', phpunit_prefix)
elif M.get('phpunit_prefix') != phpunit_prefix:
    debug('Excepted value for phpunit_prefix is \'%s\'. Please manually fix.' % phpunit_prefix)
    sys.exit(1)

# Run cli
try:
    M.initPHPUnit()
except Exception as e:
    debug(e)
    sys.exit(1)

debug('PHP Unit ready!')
