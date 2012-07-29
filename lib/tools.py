#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shlex
import subprocess

def debug(str):
	print str

def process(cmd, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
	if type(cmd) != 'list':
		cmd = shlex.split(str(cmd))
	proc = subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr)
	(out, err) = proc.communicate()
	return (proc.returncode, out, err)
