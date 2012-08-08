#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import subprocess, shlex
import re

def yesOrNo(q):
	answers = ['y', 'n']
	while True:
		i = raw_input('%s (y/n) ' % (q)).strip().lower()
		if i == 'y':
			return True
		elif i == 'n':
			return False

def debug(str):
	print str
	sys.stdout.flush()

def parseBranch(branch, pattern):
	pattern = re.compile(pattern, flags=re.I)
	result = pattern.search(branch)
	if not result:
		return False
	result = {
		'issue': result.group(pattern.groupindex['issue']),
		'version': result.group(pattern.groupindex['version'])
	}
	try:
		result['suffix'] = result.group(pattern.groupindex['suffix'])
	except:
		result['suffix'] = None
	return result

def process(cmd, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
	if type(cmd) != 'list':
		cmd = shlex.split(str(cmd))
	proc = subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr)
	(out, err) = proc.communicate()
	return (proc.returncode, out, err)

def stableBranch(version):
	if version == 'master':
		return 'master'
	return 'MOODLE_%d_STABLE' % int(version)
