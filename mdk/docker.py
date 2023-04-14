"""
Moodle Development Kit

Copyright (c) 2023 Frédéric Massart - FMCorz.net

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
import os
import shutil

from .git import Git
from .config import Conf
from .tools import process

C = Conf()


class DockerFacade():

    def __init__(self, dockerbin=None, cwd=None, env=None):
        self.dockerbin = dockerbin or '/home/fmc/code/clones/moodle-docker/bin/moodle-docker-compose'
        self.cwd = cwd or '/home/fmc/code/clones/moodle-docker'
        self.env = env or {}

    def command(self, cmd, **kwargs):
        addtoenv = kwargs.pop('addtoenv', {}).copy()
        addtoenv.update(self.env)
        return process([self.dockerbin] + cmd, cwd=self.cwd, addtoenv=addtoenv, **kwargs)


class MoodleDockerKnowAbout():
    """
    Moodle Docker Know About.

    Just a class that knows about moodle-docker.git, it's essentially only meant to be
    used to retriev the path to the project. But it also contains the prepare and update
    methods to handle a git clone, while allowing for a place reference to a folder in
    the future by extending this class.
    """

    _git = None
    _path = None
    _prepared = False

    def __init__(self, path, giturl, gitbin, gitref):
        self._path = path
        self.giturl = giturl
        self.gitbin = gitbin
        self.gitref = gitref

    @property
    def git(self):
        if not self._git:
            self._git = Git(self._path)
        return self._git

    @property
    def path(self):
        if not self._prepared:
            self.prepare()
            self._prepared = True
        return self._path

    def _checkout(self):
        gitref = f'origin/{self.gitref}'
        if self.git.currentBranch() != gitref:
            if not self.git.checkout(gitref):
                raise Exception(f'Failed to checkout ref {gitref}')

    def prepare(self):
        """Prepare the usage of moodle-docker."""

        if self._prepared:
            return

        path = self._path
        if not os.path.isdir(path):
            logging.info('Cloning moodle-docker.git')
            returncode, _, _ = process(f'{self.gitbin} clone {self.giturl} {path}')
            if returncode != 0:
                shutil.rmtree(path)
                raise Exception('Failed to clone moodle-docker.git')

            self._git = None

        self._checkout()

    def update(self):
        """Update the project."""
        self.prepare()

        logging.info('Updating moodle-docker.git')
        remote = 'origin'
        if not self.git.fetch(remote):
            raise Exception(f'Failed to fetch {remote}')

        self._checkout()