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
from .tools import question
from .config import Conf
from urlparse import urlparse
from datetime import datetime
import re
import logging
import os
import requests
import mimetypes
from tools import launchEditor, yesOrNo
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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Jira, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.version = {}
        self._load()

    def deleteAttachment(self, attachmentId):
        """Deletes an attachment"""
        resp = self.request('attachment/%s' % str(attachmentId), method='DELETE')
        if resp['status'] != 204:
            raise JiraException('Could not delete the attachment')
        return True

    def download(self, url, dest):
        """Download a URL to the destination while authenticating the user"""

        r = requests.get(url, auth=requests.auth.HTTPBasicAuth(self.username, self.password))
        if r.status_code == 403:
            raise JiraException('403 Request not authorized. %s %s' % ('GET', url))

        data = r.text
        if len(data) > 0:
            f = open(dest, 'w')
            f.write(data)
            f.close()

        return os.path.isfile(dest)

    def get(self, param, default=None):
        """Returns a property of this instance"""
        return self.info().get(param, default)

    def getAttachments(self, key):
        """Get a dict of attachments

            The keys are the filenames, the values are another dict containing:
            - id: The file ID on the Tracker
            - filename: The file name
            - URL: The URL to download the file
            - date: A datetime object representing the date at which the file was created
            - mimetype: The mimetype of the file
            - size: The size of the file in bytes
            - author: The username of the author of the file
        """
        issueInfo = self.getIssue(key, fields='attachment')
        results = issueInfo.get('fields').get('attachment', [])
        attachments = {}
        for attachment in results:
            attachments[attachment.get('filename')] = {
                'id': attachment.get('id'),
                'filename': attachment.get('filename'),
                'url': attachment.get('content'),
                'date': Jira.parseDate(attachment.get('created')),
                'mimetype': attachment.get('mimeType'),
                'size': attachment.get('size'),
                'author': attachment.get('author', {}).get('name'),
            }
        return attachments

    def getIssue(self, key, fields='*all,-comment'):
        """Load the issue info from the jira server using a rest api call.

        The returned key 'named' of the returned dict is organised by name of the fields, not id.
        """

        querystring = {'fields': fields, 'expand': 'names'}
        resp = self.request('issue/%s' % (str(key)), params=querystring)

        if resp['status'] == 404:
            raise JiraIssueNotFoundException('Issue could not be found.')
        elif not resp['status'] == 200:
            raise JiraException('The tracker is not available.')

        issue = resp['data']
        issue['named'] = {}
        issue['namedmapping'] = {}

        # Populate the named fields in a separate key. Allows us to easily find them without knowing the field ID.
        namelist = issue.get('names', {})
        for fieldkey, fieldvalue in issue.get('fields', {}).items():
            if namelist.get(fieldkey, None) != None:
                issue['named'][namelist.get(fieldkey)] = fieldvalue
                issue['namedmapping'][namelist.get(fieldkey)] = fieldkey

        return issue

    def getPullInfo(self, key):
        """Get the pull information organised by branch"""

        fields = self.getIssue(key).get('named')
        infos = {
            'repo': None,
            'branches': {}
        }

        for key, value in C.get('tracker.fieldnames').iteritems():
            if key == 'repositoryurl':
                infos['repo'] = fields.get(value)

            elif key == 'master' or key.isdigit():
                infos['branches'][key] = {
                    'branch': fields.get(value['branch']),
                    'compare': fields.get(value['diffurl'])
                }
            else:
                # We don't know that field...
                continue

        return infos

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

    def isSecurityIssue(self, key):
        """Return whether or not the issue could be a security issue"""
        resp = self.getIssue(key, fields='security')
        return True if resp.get('fields', {}).get('security', None) != None else False

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

    def request(self, uri, method='GET', data='', params={}, headers={}, files=None):
        """Sends a request to the server and returns the response status and data"""

        url = self.url + self.uri + '/rest/api/' + str(self.apiversion) + '/' + uri.strip('/')

        # Define method to method to use.
        method = method.upper()
        if method == 'GET':
            call = requests.get
        elif method == 'POST':
            call = requests.post
        elif method == 'PUT':
            call = requests.put
        elif method == 'DELETE':
            call = requests.delete
        else:
            raise JiraException('Unimplemented method')

        # Headers.
        if not files:
            headers['Content-Type'] = 'application/json'

        # Call.
        r = call(url, params=params, data=data, auth=requests.auth.HTTPBasicAuth(self.username, self.password),
                headers=headers, files=files)
        if r.status_code == 403:
            raise JiraException('403 Request not authorized. %s %s' % (method, uri))

        try:
            data = r.json()
        except:
            data = r.text

        return {'status': r.status_code, 'data': data}

    @staticmethod
    def parseDate(value):
        """Parse a date returned by Jira API and returns a datetime object."""
        # Strips the timezone information because of some issues with %z.
        value = re.sub(r'[+-]\d+$', '', value)
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')

    def search(self, query):
        return self.request('search', params={'jql': query, 'fields': 'id'})

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
                # Map the label of the field with the field code.
                fieldKey = None
                for k, v in issue.get('names').iteritems():
                    if v == updatename:
                        fieldKey = k
                        break
                if not fieldKey:
                    raise JiraException('Could not find the field named \'%s\'' % (updatename))
                update['fields'][fieldKey] = updatevalue

        if not update['fields']:
            # No fields to update.
            logging.info('No updates required')
            return True

        resp = self.request('issue/%s' % (str(key)), method='PUT', data=json.dumps(update))

        if resp['status'] != 204:
            raise JiraException('Issue was not updated: %s' % (str(resp['status'])))

        return True

    def upload(self, key, filepath):
        """Uploads a new attachment to the issue"""

        uri = 'issue/' + key + '/attachments'

        mimetype = mimetypes.guess_type(filepath)[0]
        if not mimetype:
            mimetype = 'application/octet-stream'

        files = {
            'file': (os.path.basename(filepath), open(filepath, 'rb'), mimetype)
        }

        headers = {
            'X-Atlassian-Token': 'nocheck'
        }

        resp = self.request(uri, method='POST', files=files, headers=headers)
        if resp.get('status') != 200:
            raise JiraException('Could not upload file to Jira issue')

        return True

    def getLabels(self, key):
        """Get a dict of labels
        """
        issueInfo = self.getIssue(key, fields='labels')
        return issueInfo.get('fields').get('labels', [])

    def addLabels(self, key, newLabels):
        labels = self.getLabels(key)

        results = {
            'added': [],
            'nochange': []
        }

        for label in newLabels:
            label = unicode(label)
            if label not in labels:
                labels.append(label)
                results['added'].append(label)
            else:
                results['nochange'].append(label)

        update = {'fields': {'labels': labels}}
        resp = self.request('issue/%s' % (str(key)), method='PUT', data=json.dumps(update))

        if resp['status'] != 204:
            raise JiraException('Issue was not updated: %s' % (str(resp['status'])))

        return results

    def removeLabels(self, key, oldLabels):
        labels = self.getLabels(key)

        results = {
            'removed': [],
            'nochange': []
        }

        for label in oldLabels:
            label = unicode(label)
            if label in labels:
                labels.remove(label)
                results['removed'].append(label)
            else:
                results['nochange'].append(label)

        update = {'fields': {'labels': labels}}
        resp = self.request('issue/%s' % (str(key)), method='PUT', data=json.dumps(update))

        if resp['status'] != 204:
            raise JiraException('Issue was not updated: %s' % (str(resp['status'])))

        return results

    def getTransitions(self, key):
        resp = self.request('issue/%s/transitions?expand=transitions.fields' % (str(key)), method='GET')
        if resp['status'] != 200:
            raise JiraException('Issue transitions unavailable: %s' % (str(resp['status'])))

        transitions = {}
        for transition in resp['data'].get('transitions'):
            transitions[transition.get('name')] = transition

        return transitions

    def getTransition(self, key, targetTransition):
        transitions = self.getTransitions(key)

        if targetTransition not in transitions:
            raise JiraException('Unable to change status to "%s"' % (targetTransition))

        return transitions[targetTransition]

    def makeTransition(self, key, issue, transition, fields={}, update={}):
        data = {
            'transition': {
                'id': transition.get('id')
            },
            'fields': fields,
            'update': update
        }

        resp = self.request('issue/%s/transitions' % (str(key)), method='POST', data=json.dumps(data))

        if resp['status'] != 204:
            raise JiraException('Issue was not updated: %s' % (str(resp['status'])))

        changes = {
            'data': data,
            'original': issue,
            'transition': transition
        }
        return changes

    def getComment(self):
        success = None
        while True:
            tmpfile = launchEditor(suffix='.md')
            comment = None
            with open(tmpfile, 'r') as f:
                comment = f.read()
                f.close()

            if comment == '':
                logging.error('I could not detect any file content. Did you save properly?')
                if yesOrNo('Would you like to continue editing? If not the changes will be discarded.'):
                    continue
                else:
                    return
            else:
                return comment



    def reviewStart(self, key):
        requestedTransition = self.getTransition(key, 'Start peer review')

        namedMappings = {}
        for fieldkey, fieldvalue in requestedTransition.get('fields', {}).items():
            namedMappings[fieldvalue.get('name')] = fieldkey

        issueInfo = self.getIssue(key)

        if issueInfo['named']['Peer reviewer'] and issueInfo['named']['Peer reviewer']['name'] != self.username:
            # Check whether we're already the reviewer (that would be nice)
            raise JiraException('Issue already has a peer reviewer: %s' % (str(issueInfo['named']['Peer reviewer']['name'])))

        fields = {
            namedMappings['Peer reviewer']: {
                'name': self.username
            }
        }
        return self.makeTransition(key, issueInfo, requestedTransition, fields)

    def reviewFail(self, key):
        requestedTransition = self.getTransition(key, 'Fail peer review')

        namedMappings = {}
        for fieldkey, fieldvalue in requestedTransition.get('fields', {}).items():
            namedMappings[fieldvalue.get('name')] = fieldkey

        issueInfo = self.getIssue(key)

        if not issueInfo['named']['Peer reviewer'] or issueInfo['named']['Peer reviewer']['name'] != self.username:
            # Check whether we're already the reviewer (that would be nice)
            raise JiraException('You are not the peer reviewer: %s' % (str(issueInfo['named']['Peer reviewer']['name'])))

        update = {'comment': []}

        # Attempt to add a comment.
        comment = self.getComment()
        if comment:
            update['comment'].append(
                {
                    'add': {
                        'body': comment
                    }
                }
            )

        return self.makeTransition(key, issueInfo, requestedTransition, {}, update)

class JiraException(Exception):
    pass


class JiraIssueNotFoundException(JiraException):
    pass
