#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shlex
import subprocess
import sys

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

def process(cmd, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
	if type(cmd) != 'list':
		cmd = shlex.split(str(cmd))
	proc = subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr)
	(out, err) = proc.communicate()
	return (proc.returncode, out, err)
