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

#import os
import json

from tools import debug, process
from config import C
from getpass import getpass
from restkit import request, BasicAuth

class Jira(object):

    serverurl = ''
    username = ''
    password = ''
    apiversion = '2'
    config = None
    version = None

    _loaded = False

    def __init__(self):
        self.config = {}
        self.version = {}
        self._load()

    def get(self, param, default = None):
        """Returns a property of this instance"""
        info = self.info()
        try:
            return info[param]
        except:
            return default

    def info(self):
        """Returns a dictionary of information about this instance"""
        info = {}
        self._load()
        for (k, v) in self.config.items():
            info[k] = v
        for (k, v) in self.version.items():
            info[k] = v
        return info

    def get_issue(self, key):
        """Load the version info from the jira server using a rest api call"""

        requesturl = self.url + 'rest/api/' + self.apiversion + '/issue/' + key + '?expand=names'
        response = request(requesturl, filters=[self.auth]);

        if response.status_int == 404:
            raise Exception('Issue could not be found.')

        if not response.status_int == 200:
            raise Exception('Jira is not available.')

        issue = json.loads(response.body_string())
        return issue

    def get_server_info(self):
        """Load the version info from the jira server using a rest api call"""

        requesturl = self.url + 'rest/api/' + self.apiversion + '/serverInfo'
        response = request(requesturl, filters=[self.auth]);

        if not response.status_int == 200:
            raise Exception('Jira is not available: ' + response.status)

        serverinfo = json.loads(response.body_string())
        self.version = serverinfo

    def _load(self):
        """Loads the information"""

        if self._loaded:
            return True

        # First get the jira details from the config file
        self.url = C.get('jira.url')
        self.username = C.get('jira.username')
        self.password = getpass('Jira password for user %s:' % self.username)

        # Testing basic auth
        self.auth = BasicAuth(self.username, self.password)


        if not self.url or not self.username or not self.password:
            raise Exception('Jira has not been configured in the config file.')

        self.get_server_info()

        self._loaded = True
        return True

    def set_custom_fields(self, key, updates):
        """ Set a list of fields for this issue in Jira

        The updates parameter is a dictionary of key values where the key is the custom field name
        and the value is the new value to set. This only works for fields of type text.
        """
        issue = self.get_issue(key)

        # print json.dumps(issue, indent=4)

        customfieldkey = ''
        namelist = {}

        update = { 'fields' : {} }
        namelist = issue['names']

        for fieldkey in issue['fields']:
            field = issue['fields'][fieldkey]

            for updatename in updates:
                updatevalue = updates[updatename]
                if namelist[fieldkey] == updatename:
                    if not field or field != updatevalue:
                        update['fields'][fieldkey] = updatevalue

        if not update['fields']:
            # No fields to update
            debug('No Jira updates required')
            return True

        requesturl = self.url + 'rest/api/' + self.apiversion + '/issue/' + key
        response = request(requesturl, filters=[self.auth], method='PUT', body=json.dumps(update), headers={'Content-Type' : 'application/json'});

        if response.status_int != 204:
            raise Exception('Issue was not updated:' + response.status)

        return True

    def reload(self):
        """Reloads the information"""
        self._loaded = False
        return self._load()


# Some testing functions for this class
if __name__ == "__main__":
    # Get server info

    server = Jira()

    info = server.info()

    print info

    server.set_custom_fields('MDL-37148', {'Pull  from Repository': 'git://github.com/damyon/moodle.git'})

