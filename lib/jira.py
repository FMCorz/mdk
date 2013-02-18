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

import json

from tools import debug, process
from config import Conf
import getpass
import keyring
from restkit import request, BasicAuth

C = Conf()

class Jira(object):

    serverurl = ''
    username = ''
    password = ''
    apiversion = '2'
    version = None

    _loaded = False

    def __init__(self):
        self.version = {}
        self._load()

    def get(self, param, default = None):
        """Returns a property of this instance"""
        return self.info().get(param, default)

    def info(self):
        """Returns a dictionary of information about this instance"""
        info = {}
        self._load()
        for (k, v) in self.version.items():
            info[k] = v
        return info

    def get_issue(self, key):
        """Load the issue info from the jira server using a rest api call"""

        requesturl = self.url + 'rest/api/' + self.apiversion + '/issue/' + key + '?expand=names'
        response = request(requesturl, filters=[self.auth]);

        if response.status_int == 404:
            raise JiraException('Issue could not be found.')

        if not response.status_int == 200:
            raise JiraException('Jira is not available.')

        issue = json.loads(response.body_string())
        return issue

    def get_server_info(self):
        """Load the version info from the jira server using a rest api call"""

        requesturl = self.url + 'rest/api/' + self.apiversion + '/serverInfo'
        response = request(requesturl, filters=[self.auth]);

        if not response.status_int == 200:
            raise JiraException('Jira is not available: ' + response.status)

        serverinfo = json.loads(response.body_string())
        self.version = serverinfo

    def _load(self):
        """Loads the information"""

        if self._loaded:
            return True

        # First get the jira details from the config file.
        self.url = C.get('jira.url')
        self.username = C.get('jira.username')
        # str() is needed because keyring does not handle unicode.
        self.password = keyring.get_password('mdk-jira-password', str(self.username))

        if not self.url or not self.username:
            raise JiraException('Jira has not been configured in the config file.')

        while not self._loaded:

            # Testing basic auth
            if self.password:
                self.auth = BasicAuth(self.username, self.password)

                try:
                    self.get_server_info()
                    self._loaded = True
                except JiraException:
                    print 'Either the password is incorrect or you may need to enter a Captcha to continue.'
            if not self._loaded:
                self.password = getpass.getpass('Jira password for user %s:' % self.username)
        keyring.set_password('mdk-jira-password', str(self.username), str(self.password))

        return True

    def set_custom_fields(self, key, updates):
        """ Set a list of fields for this issue in Jira

        The updates parameter is a dictionary of key values where the key is the custom field name
        and the value is the new value to set. This only works for fields of type text.
        """
        issue = self.get_issue(key)

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
            raise JiraException('Issue was not updated:' + response.status)

        return True

    def reload(self):
        """Reloads the information"""
        self._loaded = False
        return self._load()

class JiraException(Exception):
    pass
