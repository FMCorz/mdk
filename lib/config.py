#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2012 Frédéric Massart - FMCorz.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

http://github.com/FMCorz/mdk
"""

import json, re, os

class Conf(object):

	filename = 'config.json'
	data = None
	path = None
	configfile = None

	def __init__(self, path = None):
		self.path = path
		self.configfile = os.path.join(self.path, self.filename)
		self.load()

	def add(self, name, value):
		"""Add a new config to the config file"""
		if self.get(name) != None:
			raise Exception('Setting already declared')
		self.set(name, value)

	def get(self, name = None):
		"""Return a setting or None if not found"""
		if name == None:
			return self.data
		name = unicode(name).split('.')
		data = self.data
		for n in name:
			try:
				data = data[n]
			except:
				data = None
				break
		return data

	def load(self, fn = None):
		"""Loads the configuration from the config file"""
		if fn == None:
			fn = self.configfile
		try:
			lines = ''
			f = open(fn, 'r')
			for l in f:
				if re.match(r'^\s*//', l): continue
				lines += l
			self.data = {}
			if len(lines) > 0:
				self.data = json.loads(lines)
			f.close()
		except:
			raise Exception('Could not load config file %s' % fn)

	def save(self):
		"""Save the settings to the config file"""
		try:
			f = open(self.configfile, 'w')
			json.dump(self.data, f, indent = 4)
			f.close()
		except Exception as e:
			print e
			raise Exception('Could not save to config file %s' % self.configfile)

	def set(self, name, value):
		"""Set a new setting"""
		value = unicode(value)
		name = unicode(name).split('.')
		count = len(name)
		data = self.data
		for i in range(count):
			n = name[i]
			if i == count -1:
				data[n] = value
				break
			else:
				try:
					data = data[n]
				except:
					data[n] = {}
					data = data[n]
		self.save()

path = os.path.join(os.path.dirname(__file__), '..')
C = Conf(path)
