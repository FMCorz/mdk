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
