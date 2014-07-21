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
import copy


class ConfigObject(object):
    """Configuration object"""
    data = None

    def __init__(self):
        self.data = {}

    def add(self, name, value):
        """Add a new config but throws an exception if already defined"""
        if self.get(name) != None:
            raise Exception('Setting already declared')
        self.set(name, value)

    def get(self, name=None, default=None):
        """Return all the settings, or the setting if name is specified.
        In case the setting is not found default is returned instead.
        """
        data = copy.deepcopy(self.data)
        if name != None:
            name = unicode(name).split('.')
            for n in name:
                try:
                    data = data[n]
                except:
                    data = default
                    break
        return data

    def getFlat(self, data=None, parent=''):
        """Return the entire data as a flat array"""
        flatten = {}
        if data == None:
            data = self.get()
        for k, v in data.items():
            newKey = '%s.%s' % (parent, k) if parent != '' else k
            if type(v) == dict:
                for k2, v2 in self.getFlat(v, newKey).items():
                    flatten[k2] = v2
            else:
                flatten[newKey] = v
        return flatten

    def load(self, data, merge=False):
        """Load up the data"""
        if merge:
            data = self.mergeData(self.data, data)
        self.data = data

    def loadFromFile(self, filepath, merge=False):
        """Load the settings from a file"""
        if not os.path.isfile(filepath):
            raise ConfigFileNotFound('Could not find the config file %s' % filepath)
        try:
            lines = ''
            f = open(filepath, 'r')
            for l in f:
                if re.match(r'^\s*//', l):
                    continue
                lines += l
            if len(lines) > 0:
                self.load(json.loads(lines), merge=merge)
            f.close()
        except:
            raise ConfigFileCouldNotBeLoaded('Could not load config file %s' % filepath)

    def mergeData(self, origData, newData):
        """Recursively merge 2 dict of data"""
        for k, v in newData.items():
            if k in origData and type(v) == dict:
                origData[k] = self.mergeData(origData[k], v)
            else:
                # Deepcopy prevents references to original object
                origData[k] = copy.deepcopy(v)
        return origData

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

    def set(self, name, value):
        """Set a new setting"""
        if type(value) == str:
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


class Config(object):
    """Generic config class"""

    files = None
    _loaded = False

    # ConfigObject storing a merge of all the config files
    data = None

    # ConfigObject for each config file
    objects = None

    def __init__(self, files=[]):
        """Creates the configuration object"""
        self.files = []
        for f in files:
            self.files.append(f)
        self.data = ConfigObject()
        self.objects = {}

    def add(self, name, value):
        """Add a new config"""
        self.data.add(name, value)

    def get(self, name=None):
        """Return a setting"""
        return self.data.get(name)

    def load(self, allowMissing=False):
        """Loads the configuration from the config files"""

        if self._loaded:
            return True

        for fn in self.files:
            self.objects[fn] = ConfigObject()
            try:
                self.objects[fn].loadFromFile(fn)
            except ConfigFileNotFound as e:
                if not allowMissing:
                    raise e
            self.data.load(self.objects[fn].get(), merge=True)

    def reload(self):
        """Reload the configuration"""
        self._loaded = False
        self.load()

    def remove(self, name):
        """Remove a setting"""
        self.data.remove(name)

    def save(self, to, confObj=None):
        """Save the settings to the config file"""
        if not confObj:
            confObj = self.data
        try:
            f = open(to, 'w')
            json.dump(confObj.get(), f, indent=4)
            f.close()
        except Exception as e:
            print e
            raise ConfigFileCouldNotBeSaved('Could not save to config file %s' % to)

    def set(self, name, value):
        """Set a new setting"""
        self.data.set(name, value)


class Conf(Config):
    """MDK config class"""

    userFile = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Conf, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, userfile=None):
        if userfile == None:
            userfile = os.path.expanduser('~/.moodle-sdk/config.json')
        self.userFile = userfile
        files = [
            os.path.join(os.path.dirname(__file__), 'config-dist.json'),
            os.path.join(os.path.dirname(__file__), 'config.json'),
            '/etc/moodle-sdk/config.json',
            self.userFile,
        ]
        Config.__init__(self, files)
        self.load(allowMissing=True)

    def add(self, name, value):
        """Set a new setting"""
        super(Conf, self).add(name, value)
        self.save()

    def remove(self, name):
        """Remove a setting"""
        # We need to remove from the object we use as a reference in save().
        self.objects[self.userFile].remove(name)
        super(Conf, self).remove(name)
        self.save()

    def save(self, to=None, confObj=None):
        """Save only the difference to the user config file"""

        # The base file to use is the user file
        to = self.userFile
        diffData = self.objects[self.userFile]

        files = list(self.files)
        files.reverse()

        # Each of the know settings will be checked
        data = self.data.getFlat()
        for k in sorted(data.keys()):
            v = data[k]
            different = False
            found = False

            # Respect the files order when reading the settings
            for f in files:
                o = self.objects[f]
                ov = o.get(k)

                # The value hasn't been found and is different
                if not found and ov != None and ov != v:
                    different = True
                    break
                # The value is set
                elif ov != None and ov == v:
                    found = True

            # The value differs, or none of the file define it
            if different or not found:
                diffData.set(k, v)

        confObj = diffData
        super(Conf, self).save(to, confObj)

    def set(self, name, value):
        """Set a new setting"""
        super(Conf, self).set(name, value)
        self.save()


class ConfigFileNotFound(Exception):
    pass


class ConfigFileCouldNotBeLoaded(Exception):
    pass


class ConfigFileCouldNotBeSaved(Exception):
    pass
