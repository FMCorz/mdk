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

import logging
import re
import shlex
import subprocess


class Git(object):

    _path = None
    _bin = None

    def __init__(self, path, bin='/usr/bin/git'):
        self.setPath(path)
        self.setBin(bin)

    def add(self, path):
        """Add a file/path"""
        cmd = 'add %s' % (path)
        result = self.execute(cmd)
        return result[0] == 0

    def addRemote(self, name, remote):
        cmd = 'remote add %s %s' % (name, remote)
        result = self.execute(cmd)
        return result[0] == 0

    def apply(self, files):
        if type(files) == list:
            files = ' '.join(files)
        cmd = 'apply --check %s' % (files)
        result = self.execute(cmd)
        if result[0] != 0:
            return False
        cmd = 'am %s' % (files)
        result = self.execute(cmd)
        return result[0] == 0

    def checkout(self, branch):
        if self.currentBranch == branch:
            return True
        cmd = 'checkout %s' % branch
        result = self.execute(cmd)
        return result[0] == 0

    def commit(self, filepath=None):
        """Wrapper for the commit command"""
        cmd = 'commit'
        if filepath:
            cmd += ' -F %s' % (filepath)
        result = self.execute(cmd)
        return result[0] == 0

    def conflictingFiles(self):
        cmd = 'diff --name-only --diff-filter=U'
        result = self.execute(cmd)
        if result[0] == 0:
            return result[1].strip().split('\n')
        else:
            return False

    def createBranch(self, branch, track=None):
        if track != None:
            cmd = 'branch --track %s %s' % (branch, track)
        else:
            cmd = 'branch %s' % branch

        result = self.execute(cmd)
        return result[0] == 0

    def createPatch(self, ref, saveTo=None):
        cmd = 'format-patch %s --stdout' % (ref)
        result = self.execute(cmd)
        if result[0] != 0:
            return False
        elif saveTo != None:
            with open(saveTo, 'w') as f:
                f.write(result[1])
                return True
            return False
        return result[1]

    def currentBranch(self):
        cmd = 'symbolic-ref -q HEAD'
        result = self.execute(cmd)
        if result[0] != 0:
            return 'HEAD'
        else:
            return result[1].replace('refs/heads/', '').strip()

    def delRemote(self, remote):
        cmd = 'remote rm %s' % remote
        result = self.execute(cmd)
        return result[0] == 0

    def execute(self, cmd, path=None):
        if path == None:
            path = self.getPath()

        if not self.isRepository(path):
            raise Exception('This is not a Git repository')

        if not type(cmd) == list:
            cmd = shlex.split(str(cmd))
        cmd.insert(0, self.getBin())

        logging.debug(' '.join(cmd))

        try:
            proc = subprocess.Popen(cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=path
            )
            (stdout, stderr) = proc.communicate()
        except KeyboardInterrupt as e:
            proc.kill()
            raise e

        return (proc.returncode, stdout, stderr)

    def fetch(self, remote='', ref=''):
        cmd = 'fetch %s %s' % (remote, ref)
        result = self.execute(cmd)
        return result[0] == 0

    def getConfig(self, name):
        cmd = 'config --get %s' % name
        result = self.execute(cmd)
        if result[0] == 0:
            return result[1].strip()
        else:
            return None

    def getRemote(self, remote):
        remotes = self.getRemotes()
        return remotes.get(remote, None)

    def getRemotes(self):
        """Return the remotes"""
        cmd = 'remote -v'
        result = self.execute(cmd)
        remotes = None
        if result[0] == 0:
            remotes = {}
            for line in result[1].split('\n'):
                if not line: continue
                (remote, repo) = re.split('\s+', line, 1)
                repo = re.sub(' \(push\)|\(fetch\)$', '', repo)
                remotes[remote] = repo
        return remotes

    def hasBranch(self, branch, remote=''):
        if remote != '':
            cmd = 'show-ref --verify --quiet "refs/remotes/%s/%s"' % (remote, branch)
        else:
            cmd = 'show-ref --verify --quiet "refs/heads/%s"' % branch
        (returncode, stdout, stderr) = self.execute(cmd)
        return returncode == 0

    def hashes(self, ref='', format='%H', limit=30):
        """Returns the latest hashes from git log"""
        hashlist = self.log(count=limit, format=format, since=ref)
        return hashlist.split('\n')[:-1]

    def isRepository(self, path=None):
        if path == None:
            path = self.getPath()

        cmd = shlex.split(str('%s log -1') % self.getBin())
        proc = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=path
        )
        proc.wait()
        return proc.returncode == 0

    def log(self, count=10, since=None, path=None, format=None):
        """Calls the log command and returns the raw output"""
        cmd = 'log'
        if count != None and count != 0:
            cmd += ' -n %d ' % (int(count))
        if format != None:
            cmd += ' --format=%s ' % (format)
        if since != None:
            cmd += ' %s ' % (since)
        if path != None:
            cmd += ' -- %s' % (path)

        (returncode, stdout, stderr) = self.execute(cmd)
        if returncode != 0:
            raise GitException('Error calling git log. Command: %s' % (cmd))

        return stdout

    def merge(self, ref):
        """Wrapper for the merge command"""
        cmd = 'merge %s' % (ref)
        (returncode, stdout, stderr) = self.execute(cmd)
        return returncode == 0

    def messages(self, count=10, since=None, path=None):
        """Return the latest titles of the commit messages"""
        messages = self.log(count=count, since=since, path=path, format='%s')
        return messages.split('\n')[:-1]

    def pick(self, refs=None, abort=None, continu=None):
        """Wrapper for the cherry-pick command

        The typo in the argument 'continu' is voluntarily there, continue is a reserved word.
        """
        args = ''
        if refs != None:
            if type(refs) == list:
                refs = ' '.join(refs)
            args = refs
        elif abort != None:
            args = '--abort'
        elif continu != None:
            args = '--continue'
        cmd = 'cherry-pick %s' % (args)
        return self.execute(cmd)

    def pull(self, remote='', ref=''):
        cmd = 'pull %s %s' % (remote, ref)
        return self.execute(cmd)

    def push(self, remote='', branch='', force=None):
        if force:
            force = '--force '
        else:
            force = ''
        cmd = 'push %s%s %s' % (force, remote, branch)
        return self.execute(cmd)

    def rebase(self, base=None, branch=None, abort=False):
        cmd = None
        if abort:
            cmd = 'rebase --abort'
        elif base != None and branch != None:
            # Rebase automatically checks out the branch before rebasing
            cmd = 'rebase %s %s' % (base, branch)
        if cmd == None:
            raise Exception('Missing arguments for calling rebase')
        return self.execute(cmd)

    def remoteBranches(self, remote):
        pattern = 'refs/remotes/%s' % remote
        cmd = 'show-ref'

        result = self.execute(cmd)
        if result[0] != 0:
            return []

        refs = []
        for ref in result[1].split('\n'):
            try:
                (hash, ref) = ref.split(' ', 1)
            except ValueError:
                continue
            if not ref.startswith(pattern):
                continue
            ref = ref.replace(pattern, '').strip('/')
            if ref == 'HEAD':
                continue
            refs.append([hash, ref])
        return refs

    def reset(self, to, hard=False):
        mode = ''
        if hard:
            mode = '--hard'
        cmd = 'reset %s %s' % (mode, to)
        result = self.execute(cmd)
        return result[0] == 0

    def setConfig(self, name, value):
        cmd = 'config %s %s' % (name, value)
        result = self.execute(cmd)
        return result[0] == 0

    def setRemote(self, remote, url):
        if not self.getRemote(remote):
            cmd = 'remote add %s %s' % (remote, url)
        else:
            cmd = 'remote set-url %s %s' % (remote, url)
        result = self.execute(cmd)
        return result[0] == 0

    def stash(self, command='save', untracked=False):
        cmd = 'stash %s' % command
        if untracked:
            cmd += ' --include-untracked'
        return self.execute(cmd)

    def status(self):
        return self.execute('status')

    def getBin(self):
        return self._bin

    def setBin(self, bin):
        self._bin = str(bin)

    def getPath(self):
        return self._path

    def setPath(self, path):
        self._path = str(path)


class GitException(Exception):
    pass
