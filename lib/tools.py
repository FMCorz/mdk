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

import sys
import os
import subprocess
import shlex
import re
import threading


def yesOrNo(q):
    while True:
        i = raw_input('%s (y/n) ' % (q)).strip().lower()
        if i == 'y':
            return True
        elif i == 'n':
            return False


def question(q, default=None, options=None):
    """Asks the user a question, and return the answer"""
    text = q
    if default != None:
        text = text + ' [%s]' % str(default)
    i = raw_input('%s\n  ' % text)
    if i.strip() == '':
        return default
    else:
        if options != None and i not in options:
            return question(q, default, options)
        return i


def chmodRecursive(path, chmod):
    os.chmod(path, chmod)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for d in dirnames:
            dir = os.path.join(dirpath, d)
            os.chmod(dir, chmod)
        for f in filenames:
            file = os.path.join(dirpath, f)
            os.chmod(file, chmod)


def get_current_user():
    """Attempt to get the currently logged in user"""
    username = 'root'
    import os
    try:
        username = os.getlogin()
    except OSError:
        import getpass
        try:
            username = getpass.getuser()
        except:
            pass
    return username


def debug(str):
    print str
    sys.stdout.flush()


def parseBranch(branch, pattern):
    pattern = re.compile(pattern, flags=re.I)
    result = pattern.search(branch)
    if not result:
        return False
    result = {
        'issue': result.group(pattern.groupindex['issue']),
        'version': result.group(pattern.groupindex['version'])
    }
    try:
        result['suffix'] = result.group(pattern.groupindex['suffix'])
    except:
        result['suffix'] = None
    return result


def process(cmd, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    if type(cmd) != 'list':
        cmd = shlex.split(str(cmd))
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr)
    (out, err) = proc.communicate()
    return (proc.returncode, out, err)


def stableBranch(version):
    if version == 'master':
        return 'master'
    return 'MOODLE_%d_STABLE' % int(version)


class ProcessInThread(threading.Thread):
    """Executes a process in a separate thread"""

    cli = None
    loop = True

    def __init__(self, cli):
        threading.Thread.__init__(self)
        self.cli = cli

    def run(self):
        process(self.cli)
