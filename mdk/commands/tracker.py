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
from ..config import Conf
from ..ansi_escape_codes import AnsiCodes

def highlightJiraText(text):
    C = Conf()
    emojimap = C.get('tracker.emoji')
    flags = re.IGNORECASE

    for key in emojimap:
        value = emojimap[key]
        text = text.replace(key, value)
    # {{monospaced}}
    text = re.sub(r'\{\{(.*?)\}\}', AnsiCodes['GREEN'] + r'\1' + AnsiCodes['RESET'], text, flags=flags)
    # {quote}
    text = re.sub(r'\{quote\}(.*?)\{quote\}', AnsiCodes['GRAY'] + r'\1' + AnsiCodes['RESET'], text, flags=flags)
    # {color:red}
    text = re.sub(
        r'\{color:(\w+)\}(.*?)\{color\}',
        lambda matchobj: "{0}{1}{2}".format(
            AnsiCodes.get(matchobj.group(1).strip().upper(), AnsiCodes['YELLOW']),
            matchobj.group(2),
            AnsiCodes['RESET'],
        ),
        text,
        flags=flags,
    )
    # *text*
    text = re.sub(r'\*(.*?)\*', AnsiCodes['CYAN'] + r'\1' + AnsiCodes['RESET'], text, flags=flags)
    # !https://image.com/image!: remove
    text = re.sub(r'\!(.*?)\!', '', text, flags=re.IGNORECASE)
    # mention
    text = re.sub(r'\[\~(.*?)\]', AnsiCodes['RED'] + r'~\1' + AnsiCodes['RESET'], text, flags=flags)
    # list
    text = re.sub(r'^\s*([\#\-\*])\s*(.*)', AnsiCodes['GREEN'] + r'\1' + AnsiCodes['RESET'] + r' \2', text, flags=flags)
    # header
    text = re.sub(r'^\s*h([1-7])\.\s*(.*)', AnsiCodes['MAGENTA'] + r'h\1.' + AnsiCodes['RESET'] + r' \2', text, flags=flags)
    # mdl
    text = re.sub(r'mdl\-(\d+)', AnsiCodes['BLUE'] + r'MDL-\1' + AnsiCodes['RESET'], text, flags=flags)
    return text


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
            ['--comments'],
            {
                'action': 'store_true',
                'help': 'include comments'
            }
        ),
        (
            ['--number'],
            {
                'action': 'store',
                'default': 5,
                'help': 'number of comments to fetch'
            }
        ),
        (
            ['--no-colors'],
            {
                'action': 'store_true',
                'help': 'Don\'t use colors'
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
        self.no_colors = args.no_colors
        """Display classic information about an issue"""
        issue = self.Jira.getIssue(self.mdl)

        title = '%s: %s' % (issue['key'], issue['fields']['summary'])
        created = datetime.strftime(Jira.parseDate(issue['fields'].get('created')), '%Y-%m-%d %H:%M')
        resolution = '' if issue['fields']['resolution'] == None else '(%s)' % (issue['fields']['resolution']['name'])
        resolutiondate = ''
        if issue['fields'].get('resolutiondate') != None:
            resolutiondate = datetime.strftime(Jira.parseDate(issue['fields'].get('resolutiondate')), '%Y-%m-%d %H:%M')
        self.printSeparator()
        for l in textwrap.wrap(title, 68, initial_indent='  ', subsequent_indent='    '):
            print(l)
        print('  {0} - {1} - {2}'.format(issue['fields']['issuetype']['name'], issue['fields']['priority']['name'], 'https://tracker.moodle.org/browse/' + issue['key']))
        status = '{0} {1} {2}'.format(issue['fields']['status']['name'], resolution, resolutiondate).strip()
        print('  {0}'.format(status))

        self.printSeparator()
        label = 'Components'
        if not self.no_colors:
            label = AnsiCodes['YELLOW'] + label + AnsiCodes['RESET']
        components = '{0}: {1}'.format(label, ', '.join([c['name'] for c in issue['fields']['components']]))
        for l in textwrap.wrap(components, 68, initial_indent='  ', subsequent_indent='              '):
            print(l)
        if issue['fields']['labels']:
            label = 'Labels'
            if not self.no_colors:
                label = AnsiCodes['YELLOW'] + label + AnsiCodes['RESET']
            labels = '{0}: {1}'.format(label, ', '.join(issue['fields']['labels']))
            for l in textwrap.wrap(labels, 68, initial_indent='  ', subsequent_indent='          '):
                print(l)

        vw = '[ V: %d - W: %d ]' % (issue['fields']['votes']['votes'], issue['fields']['watches']['watchCount'])
        print('{0:->70}--'.format(vw))
        self.printField('{0} ({1}) on {2}', 'Reporter', issue['fields']['reporter']['displayName'], issue['fields']['reporter']['name'], created)

        if issue['fields'].get('assignee') != None:
            self.printField('{0} ({1})', 'Assignee', issue['fields']['assignee']['displayName'], issue['fields']['assignee']['name'])
        if issue['named'].get('Peer reviewer'):
            self.printField('{0} ({1})', 'Peer reviewer', issue['named']['Peer reviewer']['displayName'], issue['named']['Peer reviewer']['name'])
        if issue['named'].get('Integrator'):
            self.printField('{0} ({1})', 'Integrator', issue['named']['Integrator']['displayName'], issue['named']['Integrator']['name'])
        if issue['named'].get('Tester'):
            self.printField('{0} ({1})', 'Tester', issue['named']['Tester']['displayName'], issue['named']['Tester']['name'])

        if args.comments:
            comments = self.Jira.getIssueComments(self.mdl, maxResults=args.number)
            self.printSeparator()
            print('Comments:')
            for comment in comments:
                self.printComment(comment, hideCommenters=['cibot'])

        if args.testing and issue['named'].get('Testing Instructions'):
            self.printSeparator()
            print('Testing instructions:')
            self.printTestingInstructions(issue['named'].get('Testing Instructions'))
        self.printSeparator()

    def printSeparator(self):
        print('-' * 72)

    def printField(self, template, label, *args):
        padding = 20
        if not self.no_colors:
            padding = 28
            label = AnsiCodes['YELLOW'] + label + AnsiCodes['RESET']
        print(label.ljust(padding) + ' : ' + template.format(*args))

    def printTestingInstructions(self, text):
        lines = text.split('\r\n')
        for l in lines:
            padding = '  '
            if not self.no_colors:
                l = highlightJiraText(l)
            print(padding + l)

    def printComment(self, comment, hideCommenters=[]):
        author = '[%s]' % (comment['author']['displayName'])
        print('{0:->70}--'.format(author))
        print()
        lines = comment['body'].replace('\n\n', '\r\n').replace('\r\n', '\n').split('\n')
        for l in lines:
            for wrapped in textwrap.wrap(l, 68):
                text = wrapped
                if not self.no_colors:
                    text = highlightJiraText(wrapped)
                print('  ' + text)
