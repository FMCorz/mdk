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
import signal
import subprocess
import shlex
import re
import threading
import getpass
import logging
import hashlib
import tempfile
from .config import Conf

C = Conf()

def yesOrNo(q):
    while True:
        i = raw_input('%s (y/n) ' % (q)).strip().lower()
        if i == 'y':
            return True
        elif i == 'n':
            return False


def question(q, default=None, options=None, password=False):
    """Asks the user a question, and return the answer"""
    text = q
    if default != None:
        text = text + ' [%s]' % str(default)

    if password:
        i = getpass.getpass('%s\n   ' % text)
    else:
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


def getMDLFromCommitMessage(message):
    """Return the MDL-12345 number from a commit message"""
    mdl = None
    match = re.match(r'MDL(-|_)([0-9]+)', message, re.I)
    if match:
        mdl = 'MDL-%s' % (match.group(2))
    return mdl


def get_current_user():
    """Attempt to get the currently logged in user"""
    username = 'root'
    try:
        username = os.getlogin()
    except OSError:
        import getpass
        try:
            username = getpass.getuser()
        except:
            pass
    return username


def launchEditor(filepath=None, suffix='.tmp'):
    """Launchs up an editor

    If filepath is passed, the content of the file is used to populate the editor.

    This returns the path to the saved file.
    """
    editor = resolveEditor()
    if not editor:
        raise Exception('Could not locate the editor')
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmpfile:
        with open(filepath, 'r') as f:
            tmpfile.write(f.read())
            tmpfile.flush()
        subprocess.call([editor, tmpfile.name])
    return tmpfile.name


def getText(suffix='.md', initialText=None):
    """Gets text from the user using an Editor

    This is a shortcut to using launchEditor as it returns text rather
    than the file in which the text entered is stored.

    When the returned value is empty, the user is asked is they want to resume.
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmpfile:
        if initialText:
            tmpfile.write(initialText)
            tmpfile.flush()
        while True:
            editorFile = launchEditor(suffix=suffix, filepath=tmpfile.name)
            text = None
            with open(editorFile, 'r') as f:
                text = f.read()

            if len(text) <= 0:
                if not yesOrNo('No content detected. Would you like to resume editing?'):
                    return ''
            else:
                return text

def md5file(filepath):
    """Return the md5 sum of a file
    This is terribly memory inefficient!"""
    return hashlib.md5(open(filepath).read()).hexdigest()


def mkdir(path, perms=0755):
    """Creates a directory ignoring the OS umask"""
    oldumask = os.umask(0000)
    os.mkdir(path, perms)
    os.umask(oldumask)


def parseBranch(branch):
    pattern = re.compile(C.get('wording.branchRegex'), flags=re.I)
    result = pattern.search(branch)
    if not result:
        return False

    parsed = {
        'issue': result.group(pattern.groupindex['issue']),
        'version': result.group(pattern.groupindex['version'])
    }
    try:
        parsed['suffix'] = result.group(pattern.groupindex['suffix'])
    except:
        parsed['suffix'] = None
    return parsed


def process(cmd, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    if type(cmd) != list:
        cmd = shlex.split(str(cmd))
    logging.debug(' '.join(cmd))
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr)
        (out, err) = proc.communicate()
    except KeyboardInterrupt as e:
        proc.kill()
        raise e
    return (proc.returncode, out, err)


def resolveEditor():
    """Try to resolve the editor that the user would want to use.
       This does actually checks if it is executable"""
    editor = C.get('editor')
    if not editor:
        editor = os.environ.get('EDITOR')
    if not editor:
        editor = os.environ.get('VISUAL')
    if not editor and os.path.isfile('/usr/bin/editor'):
        editor = '/usr/bin/editor'
    return editor


def downloadProcessHook(count, size, total):
    """Hook to report the downloading a file using urllib.urlretrieve"""
    if count <= 0:
        return
    downloaded = int((count * size) / (1024))
    total = int(total / (1024)) if total != 0 else '?'
    if downloaded > total:
        downloaded = total
    sys.stderr.write("\r  %sKB / %sKB" % (downloaded, total))
    sys.stderr.flush()


def stableBranch(version):
    if version == 'master':
        return 'master'
    return 'MOODLE_%d_STABLE' % int(version)


class ProcessInThread(threading.Thread):
    """Executes a process in a separate thread"""

    cmd = None
    cwd = None
    stdout = None
    stderr = None
    _kill = False
    _pid = None

    def __init__(self, cmd, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        threading.Thread.__init__(self)
        if type(cmd) != 'list':
            cmd = shlex.split(str(cmd))
        self.cmd = cmd
        self.cwd = cwd
        self.stdout = stdout
        self.stderr = stderr

    def kill(self):
        os.kill(self._pid, signal.SIGKILL)

    def run(self):
        logging.debug(' '.join(self.cmd))
        proc = subprocess.Popen(self.cmd, cwd=self.cwd, stdout=self.stdout, stderr=self.stderr)
        self._pid = proc.pid
        while True:
            if proc.poll():
                break

            # Reading the output seems to prevent the process to hang.
            if self.stdout == subprocess.PIPE:
                proc.stdout.read(1)
