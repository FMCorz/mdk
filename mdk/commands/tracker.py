#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2013 Frédéric Massart - FMCorz.net

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

from datetime import datetime
import textwrap
import re
from ..command import Command
from ..jira import Jira
from ..tools import parseBranch


class TrackerCommand(Command):

    _arguments = [
        (
            ['-t', '--testing'],
            {
                'action': 'store_true',
                'help': 'include testing instructions'
            }
        ),
        (
            ['issue'],
            {
                'help': 'MDL issue number. Guessed from the current branch if not specified.',
                'nargs': '?'
            }
        ),
        (
            ['--add-labels'],
            {
                'action': 'store',
                'help': 'Add the specified labels to the issue',
                'nargs': '+',
                'dest':  'addlabels'
            }
        ),
        (
            ['--remove-labels'],
            {
                'action': 'store',
                'help': 'Remove the specified labels from the issue',
                'nargs': '+',
                'dest':  'removelabels'
            }
        ),
        (
            ['--start-review'],
            {
                'action': 'store_true',
                'help': 'Change the status to Peer-review in progress and assign self as reviewer',
                'dest': 'reviewStart'
            }
        ),
        (
            ['--fail-review'],
            {
                'action': 'store_true',
                'help': 'Change the status to Peer-review in progress and assign self as reviewer',
                'dest': 'reviewFail'
            }
        ),
        (
            ['--comment'],
            {
                'action': 'store_true',
                'help': 'Add a comment to the issue',
                'dest': 'comment'
            }
        )
    ]
    _description = 'Retrieve information from the tracker'

    Jira = None
    mdl = None

    def run(self, args):

        issue = None
        if not args.issue:
            M = self.Wp.resolve()
            if M:
                parsedbranch = parseBranch(M.currentBranch())
                if parsedbranch:
                    issue = parsedbranch['issue']
        else:
            issue = args.issue

        if not issue or not re.match('(MDL|mdl)?(-|_)?[1-9]+', issue):
            raise Exception('Invalid or unknown issue number')

        self.Jira = Jira()
        self.mdl = 'MDL-' + re.sub(r'(MDL|mdl)(-|_)?', '', issue)

        changesMade = False
        labelChanges = {
            'added': [],
            'removed': [],
            'nochange': []
        }

        newComments = []
        transitionChanges = {}

        if args.addlabels:
            result = self.Jira.addLabels(self.mdl, args.addlabels)
            labelChanges['added'].extend(result['added'])
            labelChanges['nochange'].extend(result['nochange'])

            if len(result['added']):
                changesMade = True

        if args.removelabels:
            result = self.Jira.removeLabels(self.mdl, args.removelabels)
            labelChanges['removed'].extend(result['removed'])
            labelChanges['nochange'].extend(result['nochange'])

            if len(result['removed']):
                changesMade = True

        if args.reviewStart:
            transitionChanges = self.Jira.reviewStart(self.mdl)

        elif args.reviewFail:
            transitionChanges = self.Jira.reviewFail(self.mdl)

        if transitionChanges:
            changesMade = True
            if 'comment' in transitionChanges['data']['update']:
                for comment in transitionChanges['data']['update']['comment']:
                    newComments.append(comment['add'])

        if args.comment:
            newComment =self.Jira.addComment(self.mdl)
            if newComment:
                changesMade = True
                newComments.append(newComment)

        issueInfo = self.info(args)

        if changesMade or len(labelChanges['nochange']):
            if changesMade:
                print u'Changes were made to this issue:'

            if len(transitionChanges):
                print '* State changed from "%s" to "%s"' % (transitionChanges['original'].get('fields')['status']['name'], issueInfo.get('fields')['status']['name'])

            if len(labelChanges['added']):
                labels = u'{0}: {1}'.format('Labels added', ', '.join(labelChanges['added']))
                for l in textwrap.wrap(labels, 68, initial_indent='* ', subsequent_indent='    '):
                    print l

            if len(labelChanges['removed']):
                labels = u'{0}: {1}'.format('Labels removed', ', '.join(labelChanges['removed']))
                for l in textwrap.wrap(labels, 68, initial_indent='* ', subsequent_indent='    '):
                    print l

            if len(labelChanges['nochange']):
                print u'Some changes were not made to this issue:'
                labels = u'{0}: {1}'.format('Labels unchanged', ', '.join(labelChanges['nochange']))
                for l in textwrap.wrap(labels, 68, initial_indent='* ', subsequent_indent='    '):
                    print l

            if len(newComments):
                print u'* Some comments were added:'
                for comment in newComments:
                    if 'id' in comment:
                        commenturl = "%s%s/browse/%s?focusedCommentId=%s" % (self.Jira.url, self.Jira.uri, self.mdl, comment['id'])
                        commentlink = u'- %s ' % commenturl
                        print '{0:->70}--'.format(commentlink)
                    else:
                        print u'-' * 72

                    # Note: Do not wrap the comment as it's not really meant to be wrapped again. The editor may have
                    # already wrapped it, or the markdown may just look a bit crap.
                    print comment['body']

            print u'-' * 72

    def info(self, args):
        """Display classic information about an issue"""
        issue = self.Jira.getIssue(self.mdl)

        title = u'%s: %s' % (issue['key'], issue['fields']['summary'])
        created = datetime.strftime(Jira.parseDate(issue['fields'].get('created')), '%Y-%m-%d %H:%M')
        resolution = u'' if issue['fields']['resolution'] == None else u'(%s)' % (issue['fields']['resolution']['name'])
        resolutiondate = u''
        if issue['fields'].get('resolutiondate') != None:
            resolutiondate = datetime.strftime(Jira.parseDate(issue['fields'].get('resolutiondate')), '%Y-%m-%d %H:%M')
        print u'-' * 72
        for l in textwrap.wrap(title, 68, initial_indent='  ', subsequent_indent='    '):
            print l
        print u'  {0} - {1} - {2}'.format(issue['fields']['issuetype']['name'], issue['fields']['priority']['name'], u'https://tracker.moodle.org/browse/' + issue['key'])
        status = u'{0} {1} {2}'.format(issue['fields']['status']['name'], resolution, resolutiondate).strip()
        print u'  {0}'.format(status)

        if issue['fields']['labels']:
            labels = u'{0}: {1}'.format('Labels', ', '.join(issue['fields']['labels']))
            for l in textwrap.wrap(labels, 68, initial_indent='  ', subsequent_indent='    '):
                print l

        vw = u'[ V: %d - W: %d ]' % (issue['fields']['votes']['votes'], issue['fields']['watches']['watchCount'])
        print '{0:->70}--'.format(vw)
        print u'{0:<20}: {1} ({2}) on {3}'.format('Reporter', issue['fields']['reporter']['displayName'], issue['fields']['reporter']['name'], created)

        if issue['fields'].get('assignee') != None:
            print u'{0:<20}: {1} ({2})'.format('Assignee', issue['fields']['assignee']['displayName'], issue['fields']['assignee']['name'])
        if issue['named'].get('Peer reviewer'):
            print u'{0:<20}: {1} ({2})'.format('Peer reviewer', issue['named']['Peer reviewer']['displayName'], issue['named']['Peer reviewer']['name'])
        if issue['named'].get('Integrator'):
            print u'{0:<20}: {1} ({2})'.format('Integrator', issue['named']['Integrator']['displayName'], issue['named']['Integrator']['name'])
        if issue['named'].get('Tester'):
            print u'{0:<20}: {1} ({2})'.format('Tester', issue['named']['Tester']['displayName'], issue['named']['Tester']['name'])

        if args.testing and issue['named'].get('Testing Instructions'):
            print u'-' * 72
            print u'Testing instructions:'
            for l in issue['named'].get('Testing Instructions').split('\r\n'):
                print '  ' + l

        print u'-' * 72

        return issue
