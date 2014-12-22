#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2014 Frédéric Massart - FMCorz.net

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
from jenkinsapi import jenkins
from jenkinsapi.custom_exceptions import JenkinsAPIException, TimeOut
from .config import Conf

C = Conf()


class CI(object):
    """Wrapper for Jenkins"""

    _jenkins = None
    url = None
    token = None

    def __init__(self, url=None, token=None, load=True):
        self.url = url or C.get('ci.url')
        self.token = token or C.get('ci.token')
        if load:
            self.load()

    @property
    def jenkins(self):
        """The Jenkins object"""
        return self._jenkins

    def load(self):
        """Loads the Jenkins object"""

        # Resets the logging level.
        logger = logging.getLogger('jenkinsapi.job')
        logger.setLevel(logging.WARNING)
        logger = logging.getLogger('jenkinsapi.build')
        logger.setLevel(logging.WARNING)

        # Loads the jenkins object.
        self._jenkins = jenkins.Jenkins(self.url)

    def precheckRemoteBranch(self, remote, branch, integrateto, issue=None):
        """Runs the precheck job and returns the build object"""
        params = {
            'remote': remote,
            'branch': branch,
            'integrateto': integrateto
        }
        if issue:
            params['issue'] = issue

        job = self.jenkins.get_job('Precheck remote branch')

        try:
            invoke = job.invoke(build_params=params, securitytoken=self.token, invoke_pre_check_delay=0)
            invoke.block_until_not_queued(60, 2)
        except JenkinsAPIException:
            raise CIException('Failed to invoke the build, check your permissions.')
        except TimeOut:
            raise CIException('The build has been in queue for more than 60s. Aborting, please refer to: %s' % job.baseurl)

        build = invoke.get_build()
        return build


class CIException(Exception):
    pass
