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


from ..command import Command
import logging
import os
import re
import subprocess
import sys
from .. import tools

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
    _args = None
    _string_list = {}
    _M = None
    _index_being_compared = None

    def run(self, args):

        # Loading instance
        self._M = self.Wp.resolve(args.name)
        if not self._M:
            raise Exception('This is not a Moodle instance')

        self._args = args
        if not args.action == 'review':
            if not args.filename:
                raise Exception('Please specifiy the filename path')
            else:
                self.filename = args.filename

            # Build data from the file to ease the process.
            file_content = self.load_data_from_file()
            self._string_list = self.prepare_data(file_content)

        if args.action == 'add':
            if not args.string:
                raise Exception('Please specifiy the lang string.')
            new_string = args.string
            new_desc = args.desc if args.desc else ''
            index = self.add(new_string, new_desc, file_content)
            if index is not None:
                logging.info("✅ New lang string '%s' has been added." % (new_string))
                logging.info('Go to line: %s:%d' % (self.filename, index))
        elif args.action == 'sort':
            self.sort(file_content)
        elif args.action == 'review':
            issuenb = args.issue
            if not issuenb:
                parsedbranch = tools.parseBranch(self._M.currentBranch())
                if not parsedbranch:
                    raise Exception('Could not extract issue number from %s' % self._M.currentBranch())
                issuenb = parsedbranch['issue']
            self.review()

    def sort(self, content):
        sort_deprecated_strings = {}
        non_sort_deprecated_strings = []

        # Find the index of the first occurrence of "$string["
        index = next((i for i, line in enumerate(content) if '$string[' in line), None)

        if index is not None:
            # Get the lines from the beginning to just before the first "$string[" line
            header = ''.join(content[:index])

        current_group = None
        # Build data for the non-deprecated and the deprecated strings
        for line in self._string_list.values():
            if line[0] == 'deprecated':
                current_group = line[1]
                sort_deprecated_strings[current_group] = []
            elif current_group is not None:
                sort_deprecated_strings[current_group].append(line)
            else:
                non_sort_deprecated_strings.append(line)

        # Generate strings according to alphabetical order for the non-deprecated.
        sorted_non_sort_deprecated_strings = sorted(non_sort_deprecated_strings, key=lambda x: x[0])
        cleaned_list = [[item[0], item[1].rstrip('\n')+'\n'] for item in sorted_non_sort_deprecated_strings]
        content = ''
        for line in cleaned_list:
            string = line[0]
            desc = line[1]
            content += self.generate_lang_string(string, desc)

        # Generate strings according to alphabetical order for the deprecated.
        for _, value in enumerate(sort_deprecated_strings):
            sorted_data = sorted(sort_deprecated_strings[value], key=lambda x: x[0])
            sort_deprecated_strings[value] = sorted_data

        content_deprecated = ''
        for _, value in enumerate(sort_deprecated_strings):
            content_deprecated += '\n'+value
            for line in sort_deprecated_strings[value]:
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
        except Exception as e:
            raise Exception('Failed to save the file: %s', repr(e))

    def add(self, new_string, new_desc, content):

        # Avoid string identifier duplication.
        has_duplicate, has_duplicate_index = self.has_duplicate(new_string)
        if has_duplicate:
            raise Exception('The "%s" is already exist! \nGo to line: %s:%d' % (new_string, self.filename, has_duplicate_index))

        # Now only support for the actively used string.
        non_deprecated_strings = self.remove_deprecated(self._string_list)

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
        first_char = new_string[0]
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
        strings_list_sorted.append(new_string)
        strings_list_sorted.sort()

        # Get which string is the nearest from the new string
        step = None
        position = strings_list_sorted.index(new_string)
        if position == 0:
            step = 0
            target_string = strings_list_sorted[1]
        else:
            step = 1
            target_string = strings_list_sorted[position-1]

        # Get the location of the target string
        insert_index = None
        for i, line in enumerate(content):
            if line.startswith(self.generate_var_string(target_string)):
                insert_index = i
                break

        # Put the new string to the correct index.
        done = False
        insert_index = insert_index + step
        while not done:
            try:
                if content[insert_index].lower().startswith('// deprecated'):
                    insert_index = insert_index - 1
                    done = True
                elif (content[insert_index].lower().startswith("$string['") or
                        content[insert_index].lower().startswith('//')):
                    done = True
                else:
                    insert_index = insert_index + 1
            except IndexError:
                done = True

        # Ensure to put the new string without new paragraph at the top
        content.insert(
            insert_index, self.generate_lang_string(new_string, "'%s';\n" % new_desc)
        )

        # Update the file.
        try:
            self.save_new_string(content)
            return insert_index + 1
        except Exception as e:
            raise Exception('Failed to save the file: %s', repr(e))

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

    def load_data_from_file(self, filename = None):
        if filename is None:
            filename = self.filename

        file_content = []
        with open(filename, "r") as file:
            file_content = file.readlines()
        return file_content

    def prepare_data(self, content):
        string_list = {}
        current_key = None
        current_value = []
        index = None
        for i, line in enumerate(content):
            if line.startswith("$string["):
                if current_key is not None:
                    c_value = ''.join(current_value)
                    string_list[index] = [current_key, c_value]
                key, value = re.split(r'\s*=\s*', line, maxsplit=1)
                current_key = key.strip('$string[').strip("']")
                current_value = [value]
                index = i
            elif line.lower().startswith("// deprecated"):
                string_list[i] = ['deprecated', line]
            else:
                current_value.append(line)

        # Add the last key-value pair
        if current_key is not None:
            c_value = ''.join(current_value)
            string_list[index] = [current_key, c_value]

        # Sort the keys of the dictionary
        sorted_keys = sorted(string_list.keys())

        # Create a new dictionary with sorted keys
        string_list = {key: string_list[key] for key in sorted_keys}

        return string_list

    def generate_var_string(self, string):
        return "$string['%s']" % string

    def generate_lang_string(self, string, desc = ''):
        return "$string['%s'] = %s" % (string, desc)

    def has_duplicate(self, string):
        new_item_index = -1
        for key, value in self._string_list.items():
            stringid = value[0]
            if string == stringid:
                new_item_index = key + 1
                return True, new_item_index
        return False, 0

    def remove_deprecated(self, string_list):
        non_deprecated_strings = []
        for line in string_list.values():
            if line[0] == 'deprecated':
                break
            non_deprecated_strings.append(line[0])
        return non_deprecated_strings

    def save_new_string(self, content, filetarget = None):
        if filetarget is None:
            filetarget = self.filename

        newfile = "".join(content)
        f = open(filetarget, "r+")
        f.truncate(0)
        f.write(newfile)
        f.close()

    def review(self):

        total_lang = 0
        total_lang_fixed = 0

        # Reading the information about the current instance.
        currentbranch = self._M.currentBranch()

        cmd = "git log main@{1}.."+currentbranch+" --oneline | tail -1"
        firstcommit = subprocess.getoutput(cmd)
        firstcommithash = firstcommit.split()[0]

        # Get files that were modified.
        file_paths = subprocess.getoutput('git diff --name-only ' + firstcommithash + '^ HEAD')
        file_paths_list = file_paths.split("\n")
        filtered_files = [file for file in file_paths_list if "lang/en/" in file]

        cwd = os.path.realpath(os.path.abspath(os.getcwd()))
        for file in filtered_files:
            proc = subprocess.getoutput("git diff -U0 " + firstcommithash + "^ HEAD " + cwd + "/" + file + " | grep '^[+]'")
            procsplit = proc.split("\n")
            procsplit.pop(0)
            content = []
            for string in procsplit:
                content.append(string[1:] + '\n')
            string_list = self.prepare_data(content)
            index_being_compared = None
            # Remove the language string.
            for _, value in string_list.items():
                newstring = self.generate_lang_string(value[0], value[1])
                index_being_compared = self.replace_string_in_file(file, newstring)

                # Add the language string.
                self.filename = file
                file_content = self.load_data_from_file(file)
                self._string_list = self.prepare_data(file_content)
                new_string = value[0]
                # Remove the first character "'" and the last three characters "';\n" of the description.
                new_desc = value[1][1:-3]
                index_new = self.add(new_string, new_desc, file_content)
                if index_new is not None:
                    if index_being_compared != index_new:
                        logging.info("✅ The lang string '%s' has been fixed." % (new_string))
                        logging.info('Go to line: %s:%d' % (self.filename, index_new))
                        logging.info('----------------------')
                        total_lang_fixed += 1

                total_lang += 1


        logging.info('%d reviewed, %d fixed' % (total_lang, total_lang_fixed))


    def replace_string_in_file(self, file_path, target_string):
        # Open the file in read mode
        with open(file_path, 'r') as file:
            # Read the content of the file
            content = file.read()

        # Replace the target string with an empty string
        modified_content = content.replace(target_string, '', 1)

        # Open the file in write mode and write the modified content
        with open(file_path, 'w') as file:
            file.write(modified_content)

        index = content.find(target_string)
        if index != -1:
            # Find the line number
            line_number = content.count('\n', 0, index) + 1

        return line_number
