#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, re, os

class Conf():

	data = None

	def __init__(self, path = None):
		
		if path == None:
			path = os.path.join(os.path.dirname(__file__), '..', 'config.json')

		lines = ''
		f = open(path, 'r')
		for l in f:
			if re.match(r'^\s*//', l): continue
			lines += l
		self.data = json.loads(lines)
		f.close()

	def get(self, name):
		name = unicode(name).split('.')
		data = self.data
		for n in name:
			try:
				data = data[n]
			except:
				data = None
				break
		return data
