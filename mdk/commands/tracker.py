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
            ['--open'],
            {
                'action': 'store_true',
                'help': 'Open issue in browser'
            }
        ),
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

        self.mdl = 'MDL-' + re.sub(r'(MDL|mdl)(-|_)?', '', issue)

        if args.open:
            Jira.openInBrowser(self.mdl)
            return

        self.Jira = Jira()

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

        title = '%s: %s' % (issue['key'], issue['fields']['summary'])
        created = datetime.strftime(Jira.parseDate(issue['fields'].get('created')), '%Y-%m-%d %H:%M')
        resolution = '' if issue['fields']['resolution'] == None else '(%s)' % (issue['fields']['resolution']['name'])
        resolutiondate = ''
        if issue['fields'].get('resolutiondate') != None:
            resolutiondate = datetime.strftime(Jira.parseDate(issue['fields'].get('resolutiondate')), '%Y-%m-%d %H:%M')
        print('-' * 72)
        for l in textwrap.wrap(title, 68, initial_indent='  ', subsequent_indent='    '):
            print(l)
        print('  {0} - {1} - {2}'.format(issue['fields']['issuetype']['name'], issue['fields']['priority']['name'], 'https://moodle.atlassian.net/browse/' + issue['key']))
        status = '{0} {1} {2}'.format(issue['fields']['status']['name'], resolution, resolutiondate).strip()
        print('  {0}'.format(status))

        print('-' * 72)
        components = '{0}: {1}'.format('Components', ', '.join([c['name'] for c in issue['fields']['components']]))
        for l in textwrap.wrap(components, 68, initial_indent='  ', subsequent_indent='              '):
            print(l)
        if issue['fields']['labels']:
            labels = '{0}: {1}'.format('Labels', ', '.join(issue['fields']['labels']))
            for l in textwrap.wrap(labels, 68, initial_indent='  ', subsequent_indent='          '):
                print(l)

        vw = '[ V: %d - W: %d ]' % (issue['fields']['votes']['votes'], issue['fields']['watches']['watchCount'])
        print('{0:->70}--'.format(vw))
        print('{0:<20}: {1} ({2}) on {3}'.format('Reporter', issue['fields']['reporter']['displayName'], issue['fields']['reporter']['emailAddress'], created))

        if issue['fields'].get('assignee') != None:
            print('{0:<20}: {1} ({2})'.format('Assignee', issue['fields']['assignee']['displayName'], issue['fields']['assignee']['emailAddress']))
        if issue['named'].get('Peer reviewer'):
            print('{0:<20}: {1} ({2})'.format('Peer reviewer', issue['named']['Peer reviewer']['displayName'], issue['named']['Peer reviewer']['emailAddress']))
        if issue['named'].get('Integrator'):
            print('{0:<20}: {1} ({2})'.format('Integrator', issue['named']['Integrator']['displayName'], issue['named']['Integrator']['emailAddress']))
        if issue['named'].get('Tester'):
            print('{0:<20}: {1} ({2})'.format('Tester', issue['named']['Tester']['displayName'], issue['named']['Tester']['emailAddress']))

        if args.testing and issue['named'].get('Testing Instructions'):
            print('-' * 72)
            print('Testing instructions:')
            for l in issue['named'].get('Testing Instructions').split('\r\n'):
                print('  ' + l)

        print('-' * 72)
