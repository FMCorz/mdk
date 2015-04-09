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
from ..tools import parseBranch, getText


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
                'dest':  'addlabels',
                'help': 'add the specified labels to the issue',
                'metavar':  'labels',
                'nargs': '+',
            }
        ),
        (
            ['--remove-labels'],
            {
                'action': 'store',
                'dest':  'removelabels',
                'help': 'remove the specified labels from the issue',
                'metavar':  'labels',
                'nargs': '+',
            }
        ),
        (
            ['--comment'],
            {
                'action': 'store_true',
                'help': 'add a comment to the issue',
            }
        )
    ]
    _description = 'Interact with Moodle tracker'

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

        if args.addlabels:
            if 'triaged' in args.addlabels:
                self.argumentError('The label \'triaged\' cannot be added using MDK')
            elif 'triaging_in_progress' in args.addlabels:
                self.argumentError('The label \'triaging_in_progress\' cannot be added using MDK')
            self.Jira.addLabels(self.mdl, args.addlabels)

        if args.removelabels:
            if 'triaged' in args.removelabels:
                self.argumentError('The label \'triaged\' cannot be removed using MDK')
            elif 'triaging_in_progress' in args.removelabels:
                self.argumentError('The label \'triaging_in_progress\' cannot be removed using MDK')
            self.Jira.removeLabels(self.mdl, args.removelabels)

        if args.comment:
            comment = getText()
            self.Jira.addComment(self.mdl, comment)

        self.info(args)

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

        print u'-' * 72
        components = u'{0}: {1}'.format('Components', ', '.join([c['name'] for c in issue['fields']['components']]))
        for l in textwrap.wrap(components, 68, initial_indent='  ', subsequent_indent='              '):
            print l
        if issue['fields']['labels']:
            labels = u'{0}: {1}'.format('Labels', ', '.join(issue['fields']['labels']))
            for l in textwrap.wrap(labels, 68, initial_indent='  ', subsequent_indent='          '):
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
