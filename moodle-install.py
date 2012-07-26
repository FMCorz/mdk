#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import shutil
import argparse
import re

from lib import config, tools, db, moodle
Moodle = moodle.Moodle
debug = tools.debug
DB = db.DB
C = config.Conf().get

# Arguments
parser = argparse.ArgumentParser(description='Install a Moodle instance')
parser.add_argument('-i', '--integration', action='store_true', help='create an instance from integration')
parser.add_argument('-e', '--engine', action='store', choices=['mysqli', 'pgsql'], default=C('defaultEngine'), help='database engine to use', metavar='engine')
parser.add_argument('-s', '--suffix', action='store', help='suffix for the instance name', metavar='suffix')
parser.add_argument('-v', '--version', action='store', choices=['19', '20', '21', '22', '23', 'master'], default='master', help='version of Moodle', metavar='version')
parser.add_argument('--interactive', action='store_true', help='interactive mode')
parser.add_argument('--no-install', action='store_true', help='disable the installation', dest='noinstall')
args = parser.parse_args()

engine = args.engine
version = args.version

cacheStable = os.path.join(C('dirs.cache'), 'moodle.git')
cacheIntegration = os.path.join(C('dirs.cache'), 'integration.git')

# Cloning/caching repositories if necessary
if not os.path.isdir(cacheStable):
	os.chdir(C('dirs.cache'))
	os.system('git clone ' + C('remotes.stable') + ' moodle.git')
if not os.path.isdir(cacheIntegration):
	os.chdir(C('dirs.cache'))
	os.system('git clone ' +C('remotes.integration') + ' integration.git')

# Wording version
prefixVersion = version
versionNice = version
if version == 'master':
	prefixVersion = C('wording.prefixMaster')
	versionNice = C('wording.master')

# Generating parameters
if args.integration:
	name = C('wording.prefixIntegration') + prefixVersion
	fullname = C('wording.integration') + ' ' + versionNice + ' ' + C('wording.%s' % engine)
	repository = cacheIntegration
else:
	name = C('wording.prefixStable') + prefixVersion
	fullname = C('wording.stable') + ' ' + versionNice + ' ' + C('wording.%s' % engine)
	repository = cacheStable

# Append the suffix
if args.suffix:
	name += C('wording.suffixSeparator') + args.suffix
	fullname += ' ' + args.suffix.replace('-', ' ').replace('_', ' ').title()

installDir = os.path.join(C('dirs.store'), name)
wwwDir = os.path.join(installDir, C('wwwDir'))
dataDir = os.path.join(installDir, C('dataDir'))
linkDir = os.path.join(C('dirs.www'), name)

# Cloning the repository
if os.path.isdir(installDir):
	debug('Installation directory exists (%s)' % installDir)
	# sys.exit()

	# if args.interactive:
	# 	pass
	# else:
	# 	if args.force:
	# 		pass
	# 	else:
	# 		pass
else:
	os.mkdir(installDir, 0755)
	os.mkdir(dataDir, 0777)
	if C('useCacheAsRemote'):
		os.chdir(installDir)
		os.system('git clone ' + repository + ' ' + C('wwwDir'))
	else:
		shutil.copytree(repository, wwwDir)

# Checking database
dbname = re.sub(r'[^a-zA-Z0-9]', '', name).lower()[:28]
db = DB(engine, C('db.%s' % engine))
if db.dbexists(dbname):
	db.dropdb(dbname)
	db.createdb(dbname)
else:
	db.createdb(dbname)
db.selectdb(dbname)

# Installing
debug('Installing %s...' % name)
os.chdir(wwwDir)
if os.path.islink(linkDir):
	os.remove(linkDir)
if os.path.isfile(linkDir) or os.path.isdir(linkDir):	# No elif!
	debug('Could not create symbolic link')
else:
	os.symlink(wwwDir, linkDir)

# Creating, fetch, pulling branches
os.system('git fetch origin')
if version == 'master':
	branch = 'origin/master'
	os.system('git checkout master')
else:
	branch = 'origin/MOODLE_%s_STABLE' % version
	os.system('git checkout -b MOODLE_%s_STABLE %s' % (version, branch))
os.system('git pull')
os.system('git remote add mine %s' % C('remotes.mine'))
os.system('git config --local moodle.name %s' % name)
os.system('git config --local moodle.branch %s' % branch)
os.system('git config --local moodle.version %s' % version)
os.system('git config --local moodle.engine %s' % engine)

# Launching installation process
if not args.noinstall:

	os.chdir(wwwDir)
	configFile = os.path.join(wwwDir, 'config.php')
	params = (C('phpEnv'), C('host'), name, dataDir, engine, dbname, C('db.%s.user' % engine), C('db.%s.passwd' % engine), C('db.%s.host' % engine), fullname, name, C('login'), C('passwd'))
	status = os.system('%s admin/cli/install.php --wwwroot="http://%s/%s/" --dataroot="%s" --dbtype="%s" --dbname="%s" --dbuser="%s" --dbpass="%s" --dbhost="%s" --fullname="%s" --shortname="%s" --adminuser="%s" --adminpass="%s" --allow-unstable --agree-license --non-interactive' % params)
	if status != 0:
		raise Exception('Error while running the install, please manually fix the problem.')

	os.chmod(configFile, 0666)
	try:
		f = open(configFile, 'a')
		f.seek(0, os.SEEK_END)
		f.write("\n$CFG->sessioncookiepath = '/%s/';\n" % name)
		f.close()
	except Exception:
		debug('Could not append $CFG->sessioncookiepath to config.php')

