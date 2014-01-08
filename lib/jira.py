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
from tools import question
from config import Conf
from urllib import urlencode
from urlparse import urlparse
from base64 import b64encode
from datetime import datetime
import re
import logging
import os
import httplib
try:
    import keyring
except:
    # TODO Find a better way of suggesting this
    # debug('Could not load module keyring. You might want to install it.')
    # debug('Try `apt-get install python-keyring`, or visit http://pypi.python.org/pypi/keyring')
    pass

C = Conf()


class Jira(object):

    username = ''
    password = ''
    apiversion = '2'
    version = None
    url = None

    host = ''
    ssl = False
    uri = ''

    _loaded = False

    def __init__(self):
        self.version = {}
        self._load()

    def download(self, url, dest):
        """Download a URL to the destination while authenticating the user"""
        headers = {}
        headers['Authorization'] = 'Basic %s' % (b64encode('%s:%s' % (self.username, self.password)))

        if self.ssl:
            r = httplib.HTTPSConnection(self.host)
        else:
            r = httplib.HTTPConnection(self.host)
        r.request('GET', url, None, headers)

        resp = r.getresponse()
        if resp.status == 403:
            raise JiraException('403 Request not authorized. %s %s' % ('GET', url))

        data = resp.read()
        if len(data) > 0:
            f = open(dest, 'w')
            f.write(data)
            f.close()

        return os.path.isfile(dest)

    def get(self, param, default=None):
        """Returns a property of this instance"""
        return self.info().get(param, default)

    def getIssue(self, key, fields='*all,-comment'):
        """Load the issue info from the jira server using a rest api call.

        The returned key 'named' of the returned dict is organised by name of the fields, not id.
        """

        querystring = {'fields': fields, 'expand': 'names'}
        resp = self.request('issue/%s' % (str(key)), data=urlencode(querystring))

        if resp['status'] == 404:
            raise JiraException('Issue could not be found.')
        elif not resp['status'] == 200:
            raise JiraException('The tracker is not available.')

        issue = resp['data']
        issue['named'] = {}

        # Populate the named fields in a separate key. Allows us to easily find them without knowing the field ID.
        namelist = issue.get('names', {})
        for fieldkey, fieldvalue in issue.get('fields', {}).items():
            if namelist.get(fieldkey, None) != None:
                issue['named'][namelist.get(fieldkey)] = fieldvalue

        return issue

    def getServerInfo(self):
        """Load the version info from the jira server using a rest api call"""
        resp = self.request('serverInfo')
        if resp['status'] != 200:
            raise JiraException('Unexpected response code: %s' % (str(resp['status'])))

        self.version = resp['data']

    def info(self):
        """Returns a dictionary of information about this instance"""
        info = {}
        self._load()
        for (k, v) in self.version.items():
            info[k] = v
        return info

    def _load(self):
        """Loads the information"""

        if self._loaded:
            return True

        # First get the jira details from the config file.
        self.url = C.get('tracker.url').rstrip('/')
        self.username = C.get('tracker.username')

        parsed = urlparse(self.url)
        self.ssl = True if parsed.scheme == 'https' else False
        self.host = parsed.netloc
        self.uri = parsed.path

        try:
            # str() is needed because keyring does not handle unicode.
            self.password = keyring.get_password('mdk-jira-password', str(self.username))
        except:
            # Do not die if keyring package is not available.
            self.password = None

        if not self.url:
            raise JiraException('The tracker host has not been configured in the config file.')

        askUsername = True if not self.username else False
        while not self._loaded:

            # Testing basic auth
            if self.password:
                try:
                    self.getServerInfo()
                    self._loaded = True
                except JiraException:
                    askUsername = True
                    print 'Either the username and password don\'t match or you may need to enter a Captcha to continue.'
            if not self._loaded:
                if askUsername:
                    self.username = question('What is the username to use to connect to Moodle Tracker?', default=self.username if self.username else None)
                self.password = question('Enter the password for username \'%s\' on Moodle Tracker?' % self.username, password=True)

        # Save the username to the config file
        if self.username != C.get('tracker.username'):
            C.set('tracker.username', self.username)

        try:
            keyring.set_password('mdk-jira-password', str(self.username), str(self.password))
        except:
            # Do not die if keyring package is not available.
            pass

        return True

    def reload(self):
        """Reloads the information"""
        self._loaded = False
        return self._load()

    def request(self, uri, method='GET', data='', headers={}):
        """Sends a request to the server and returns the response status and data"""

        uri = self.uri + '/rest/api/' + str(self.apiversion) + '/' + uri.strip('/')
        method = method.upper()
        if method == 'GET':
            uri += '?%s' % (data)
            data = ''

        # Basic authentication
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = 'Basic %s' % (b64encode('%s:%s' % (self.username, self.password)))

        if self.ssl:
            r = httplib.HTTPSConnection(self.host)
        else:
            r = httplib.HTTPConnection(self.host)
        r.request(method, uri, data, headers)

        resp = r.getresponse()
        if resp.status == 403:
            raise JiraException('403 Request not authorized. %s %s' % (method, uri))

        data = resp.read()
        if len(data) > 0:
            try:
                data = json.loads(data)
            except ValueError:
                raise JiraException('Could not parse JSON data. Data received:\n%s' % data)

        return {'status': resp.status, 'data': data}

    @staticmethod
    def parseDate(value):
        """Parse a date returned by Jira API"""
        # Strips the timezone information because of some issues with %z.
        value = re.sub(r'[+-]\d+$', '', value)
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')

    def search(self, query):
        return self.request('search', data=urlencode({'jql': query, 'fields': 'id'}))

    def setCustomFields(self, key, updates):
        """Set a list of fields for this issue in Jira

        The updates parameter is a dictionary of key values where the key is the custom field name
        and the value is the new value to set.

        /!\ This only works for fields of type text.
        """

        issue = self.getIssue(key)
        update = {'fields': {}}

        for updatename, updatevalue in updates.items():
            remotevalue = issue.get('named').get(updatename)
            if not remotevalue or remotevalue != updatevalue:
                fieldkey = [k for k, v in issue.get('names').iteritems() if v == updatename][0]
                update['fields'][fieldkey] = updatevalue

        if not update['fields']:
            # No fields to update
            logging.info('No updates required')
            return True

        resp = self.request('issue/%s' % (str(key)), method='PUT', data=json.dumps(update))

        if resp['status'] != 204:
            raise JiraException('Issue was not updated: %s' % (str(resp['status'])))

        return True


class JiraException(Exception):
    pass
