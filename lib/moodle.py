#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from tools import debug

class Moodle():

    _path = None
    _config = None
    _installed = False
    _settings = {}

    def __init__(self, path):

        self._path = path
        self._config = os.path.join(path, 'config.php')

        if os.path.isfile(self._config):
            self.load()
            self._installed = True
        else:
            self._installed = False

    def installed(self):
        return self._installed

    def load(self):

        if not self.installed():
            return None

        # Extracts parameters from config.php, does not handle params over multiple lines
        prog = re.compile('^\s*\$CFG->([a-z]+)\s*=\s*(?P<brackets>[\'"])(.+)(?P=brackets)\s*;$', re.I)
        try:
            f = open(self._config, 'r')
            for line in f:
                match = prog.search(line)
                if match == None: continue
                self._settings[match.group(1)] = match.group(3)
                setattr(self, match.group(1), match.group(3))
            f.close()

        except Exception as e:
            debug('Error while reading config file')