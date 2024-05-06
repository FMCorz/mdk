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


import logging
from ..command import Command
import re


class LangCommand(Command):

    _arguments = [
        (
            ['action'],
            {
                'help': 'the action to perform',
                'metavar': 'action',
                'sub-commands': {
                    'add': (
                        {
                            'help': 'Adds a new string without changing the order of the old code'
                        },
                        [
                            (
                                ['string'],
                                {
                                    'metavar': 'string',
                                    'help': 'The new lang string identifier'
                                }
                            ),
                            (
                                ['-d', '--desc'],
                                {
                                    'default': '',
                                    'help': 'Description of the new string',
                                    'metavar': 'desc',
                                }
                            ),
                            (
                                ['filename'],
                                {
                                    'default': '',
                                    'metavar': 'filename',
                                    'help': 'The Absolute or relative path to a language file',
                                }
                            )
                        ]
                    ),
                    'review': (
                        {
                            'help': 'Fix the order of the new language string based on the issue being reviewed.'
                        },
                        [
                            (
                                ['issue'],
                                {
                                    'default': None,
                                    'help': 'tracker issue to review from (MDL-12345, 12345). If not specified, read from current branch.',
                                    'metavar': 'issue',
                                    'nargs': '?'
                                }
                            )
                        ]
                    ),
                    'sort': (
                        {
                            'help': 'Sort all the lang strings, including old lang string and the deprecated strings'
                        },
                        [
                            (
                                ['filename'],
                                {
                                    'default': '',
                                    'metavar': 'filename',
                                    'help': 'filename',
                                }
                            )
                        ]
                    )
                }
            }
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance to backport from. Can be omitted if branch is specified.',
                'metavar': 'name',
                'nargs': '?'
            }
        )
    ]
    _description = 'Sort lang strings alphabetically'

    deprecated_strings = {}
    sort_deprecated_strings = {}
    non_deprecated_strings = []
    non_sort_deprecated_strings = []
    file_content = []
    non_deprecated_index = {}

    def run(self, args):

        # Loading instance
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        if not args.filename:
            raise Exception('Please specifiy the filename path')
        else:
            self.filename = args.filename

        # Build data from the file to ease the process.
        self.build_data()

        if args.action == 'add':
            if not args.string:
                raise Exception('Please specifiy the lang string.')
            self.new_string = args.string
            self.new_desc = args.desc if args.desc else ''
            self.add()
        elif args.action == 'sort':
            self.sort()
        elif args.action == 'review':
            self.review()

    def sort(self):
        # Find the index of the first occurrence of "$string["
        index = next((i for i, line in enumerate(self.file_content) if '$string[' in line), None)

        if index is not None:
            # Get the lines from the beginning to just before the first "$string[" line
            header = ''.join(self.file_content[:index])

        current_group = None
        # Build data for the non-deprecated and the deprecated strings
        for line in self.non_deprecated_index.values():
            if line[0] == 'deprecated':
                current_group = line[1]
                self.sort_deprecated_strings[current_group] = []
            elif current_group is not None:
                self.sort_deprecated_strings[current_group].append(line)
            else:
                self.non_sort_deprecated_strings.append(line)

        # Generate strings according to alphabetical order for the non-deprecated.
        sorted_non_sort_deprecated_strings = sorted(self.non_sort_deprecated_strings, key=lambda x: x[0])
        cleaned_list = [[item[0], item[1].rstrip('\n')+'\n'] for item in sorted_non_sort_deprecated_strings]
        content = ''
        for line in cleaned_list:
            string = line[0]
            desc = line[1]
            content += self.generate_lang_string(string, desc)

        # Generate strings according to alphabetical order for the deprecated.
        for key, value in enumerate(self.sort_deprecated_strings):
            sorted_data = sorted(self.sort_deprecated_strings[value], key=lambda x: x[0])
            self.sort_deprecated_strings[value] = sorted_data

        content_deprecated = ''
        for key, value in enumerate(self.sort_deprecated_strings):
            content_deprecated += '\n'+value
            for line in self.sort_deprecated_strings[value]:
                string = line[0]
                desc = line[1]
                content_deprecated += self.generate_lang_string(string, desc.rstrip('\n')+'\n')

        # Get all content
        content = "%s%s%s" % (header, content, content_deprecated)

        # Save the new content to the file.
        try:
            self.save_new_string(content)
            logging.info('Lang string sorted.')
            logging.info('Go to line: %s' % (self.filename))
        except:
            raise Exception('Failed to save the file')

    def add(self):
        has_duplicate, has_duplicate_index = self.has_duplicate(self.new_string)
        if has_duplicate:
            raise Exception('The "%s" is already exist! \nGo to line: %s:%d' % (self.new_string, self.filename, has_duplicate_index))

        # Now only support for the actively used string.
        non_deprecated_strings = []
        for line in self.non_deprecated_index.values():
            if line[0] == 'deprecated':
                break
            non_deprecated_strings.append(line[0])

        letters = {}
        current_char = ''
        for string in non_deprecated_strings:
            first_char = string[0]

            if first_char != current_char:
                letters[first_char] = letters.get(first_char, [])
                letters[first_char].append([])
                current_char = first_char

            letters[first_char][-1].append(string)

        letter_groups = {key: value for key, value in letters.items()}

        # If the new_string first character is not exist then find the nearest letter
        first_char = self.new_string[0]
        while first_char not in letter_groups.keys():
            first_char = self.nearest_letter_to_list(first_char, letter_groups.keys())

        # Get strings in the letter
        data = letter_groups[first_char]

        # Look for which list has more data in the letter dict.
        max_length = 0
        current_length = 0
        max_idx = -1
        for i, d in enumerate(data):
            current_length = len(d)
            if current_length > max_length:
                max_length = current_length
                max_idx = i

        # Add the new string to the string list
        strings_list_sorted = letter_groups[first_char][max_idx]
        strings_list_sorted.append(self.new_string)
        strings_list_sorted.sort()

        # Get which string is the nearest from the new string
        step = None
        position = strings_list_sorted.index(self.new_string)
        if position == 0:
            step = 0
            target_string = strings_list_sorted[1]
        else:
            step = 1
            target_string = strings_list_sorted[position-1]

        # Get the location of the target string
        insert_index = None
        for i, line in enumerate(self.file_content):
            if line.startswith(self.generate_var_string(target_string)):
                insert_index = i
                break

        # Put the new string to the correct index.
        done = False
        insert_index = insert_index + step
        while not done:
            try:
                if self.file_content[insert_index].lower().startswith('// deprecated'):
                    insert_index = insert_index - 1
                    done = True
                elif (self.file_content[insert_index].lower().startswith("$string['") or
                        self.file_content[insert_index].lower().startswith('//')):
                    done = True
                else:
                    insert_index = insert_index + 1
            except IndexError:
                done = True

        # Ensure to put the new string without new paragraph at the top
        self.file_content.insert(
            insert_index, self.generate_lang_string(self.new_string, "'%s';\n" % self.new_desc)
        )

        # Update the file.
        try:
            self.save_new_string(self.file_content)
            logging.info('New lang string has been added.')
            logging.info('Go to line: %s:%d' % (self.filename, insert_index + 1))
        except:
            raise Exception('Failed to save the file')

    def nearest_letter_to_list(self, target_letter, letter_list):
        target_letter = target_letter.lower()  # Convert to lowercase for case-insensitivity
        letter_list = [letter.lower() for letter in letter_list]  # Convert the list to lowercase for case-insensitivity

        min_distance = float('inf')
        nearest_letter = None

        for letter in letter_list:
            distance = abs(ord(target_letter) - ord(letter))
            if distance < min_distance:
                min_distance = distance
                nearest_letter = letter

        return nearest_letter

    def build_data(self):
        current_key = None
        current_value = []
        index = None
        with open(self.filename, "r") as file:
            self.file_content = file.readlines()
            for i, line in enumerate(self.file_content):
                if line.startswith("$string["):
                    if current_key is not None:
                        c_value = ''.join(current_value)
                        self.non_deprecated_index[index] = [current_key, c_value]
                        self.non_deprecated_strings.append(current_key) # old code
                    key, value = re.split(r'\s*=\s*', line, maxsplit=1)
                    current_key = key.strip('$string[').strip("']")
                    current_value = [value]
                    index = i
                elif line.lower().startswith("// deprecated"):
                    self.non_deprecated_index[i] = ['deprecated', line]
                else:
                    current_value.append(line)

            # Add the last key-value pair
            if current_key is not None:
                c_value = ''.join(current_value)
                self.non_deprecated_index[index] = [current_key, c_value]
                self.non_deprecated_strings.append(current_key)

            # Sort the keys of the dictionary
            sorted_keys = sorted(self.non_deprecated_index.keys())

            # Create a new dictionary with sorted keys
            self.non_deprecated_index = {key: self.non_deprecated_index[key] for key in sorted_keys}

    def generate_var_string(self, string):
        return "$string['%s']" % string

    def generate_lang_string(self, string, desc = ''):
        return "$string['%s'] = %s" % (string, desc)

    def has_duplicate(self, string):
        new_item_index = -1
        if string in self.non_deprecated_strings:
            for i, line in enumerate(self.file_content):
                if line.startswith(self.generate_var_string(string)):
                    new_item_index = i + 1
                    break
            return True, new_item_index
        return False, 0

    def save_new_string(self, content):
        newfile = "".join(content)
        f = open(self.filename, "r+")
        f.truncate(0)
        f.write(newfile)
        f.close()

    def review():
        print('coming soon!')
