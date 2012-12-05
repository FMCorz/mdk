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

import os
import json
import re
from exceptions import ConfigFileCouldNotBeLoaded, ConfigFileNotFound, ConfigFileCouldNotBeSaved


class Config(object):
    """Generic config class"""

    directories = None
    filename = 'config.json'
    data = None
    configfile = None

    def __init__(self, path=None, filename=None):
        """Creates the configuration object"""
        self.directories = []
        if path != None:
            self.directories.insert(0, path)
        if filename != None:
            self.filename = filename

    def add(self, name, value):
        """Add a new config to the config file"""
        if self.get(name) != None:
            raise Exception('Setting already declared')
        self.set(name, value)

    def get(self, name=None):
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

    def load(self, fn=None):
        """Loads the configuration from the config file"""
        if fn == None:
            fn = self.resolve()
        self.configfile = fn
        try:
            lines = ''
            f = open(fn, 'r')
            for l in f:
                if re.match(r'^\s*//', l):
                    continue
                lines += l
            self.data = {}
            if len(lines) > 0:
                self.data = json.loads(lines)
            f.close()
        except:
            raise ConfigFileCouldNotBeLoaded('Could not load config file %s' % fn)

    def remove(self, name):
        """Remove a setting"""
        name = unicode(name).split('.')
        count = len(name)
        data = self.data
        for i in range(count):
            n = name[i]
            if i == (count - 1):
                try:
                    del data[n]
                except:
                    pass
                break
            else:
                try:
                    data = data[n]
                except:
                    break
        self.save()

    def resolve(self):
        """Resolve the path to the configuration file"""
        path = None
        for directory in self.directories:
            candidate = os.path.expanduser(os.path.join(directory, self.filename))
            if os.path.isfile(candidate):
                path = candidate
                break
        if path == None:
            raise ConfigFileNotFound('Could not find config file')
        return path

    def save(self):
        """Save the settings to the config file"""
        try:
            f = open(self.configfile, 'w')
            json.dump(self.data, f, indent=4)
            f.close()
        except Exception as e:
            print e
            raise ConfigFileCouldNotBeSaved('Could not save to config file %s' % self.configfile)

    def set(self, name, value):
        """Set a new setting"""
        value = unicode(value)
        name = unicode(name).split('.')
        count = len(name)
        data = self.data
        for i in range(count):
            n = name[i]
            if i == (count - 1):
                data[n] = value
                break
            else:
                try:
                    data = data[n]
                except:
                    data[n] = {}
                    data = data[n]
        self.save()


class Conf(Config):
    """MDK config class"""

    def __init__(self, path=None, filename=None):
        Config.__init__(self, path, filename)
        self.directories.append('~/.moodle-sdk/')
        self.directories.append('/etc/moodle-sdk/')
        self.directories.append(os.path.join(os.path.dirname(__file__), '..'))
        self.load()
