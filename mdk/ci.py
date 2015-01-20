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

    SUCCESS = 'S'
    FAILURE = 'F'
    ERROR = 'E'
    WARNING = 'W'

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
        """Runs the precheck job and returns the outcome"""
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
        except TimeOut:
            raise CIException('The build has been in queue for more than 60s. Aborting, please refer to: %s' % job.baseurl)
        except JenkinsAPIException:
            raise CIException('Failed to invoke the build, check your permissions.')

        build = invoke.get_build()

        logging.info('Waiting for the build to complete, please wait...')
        build.block_until_complete(3)

        # Checking the build
        outcome = CI.SUCCESS
        infos = {'url': build.baseurl}

        if build.is_good():
            logging.debug('Build complete, checking precheck results...')

            output = build.get_console()
            result = self.parseSmurfResult(output)
            if not result:
                outcome = CI.FAILURE
            else:
                outcome = result['smurf']['result']
                infos = dict(infos.items() + result.items())

        else:
            outcome = CI.FAILURE

        return (outcome, infos)

    def parseSmurfResult(self, output):
        """Parse the smurt result"""
        result = {}

        for line in output.splitlines():
            if not line.startswith('SMURFRESULT'):
                continue

            line = line.replace('SMURFRESULT: ', '')
            (smurf, rest) = line.split(':')
            elements = [smurf]
            elements.extend(rest.split(';'))
            for element in elements:
                data = element.split(',')

                errors = int(data[2])
                warnings = int(data[3])

                if errors > 0:
                    outcome = CI.ERROR
                elif warnings > 0:
                    outcome = CI.WARNING
                else:
                    outcome = CI.SUCCESS

                result[data[0]] = {
                    'errors': errors,
                    'warnings': warnings,
                    'result': outcome
                }

            break

        return result


class CIException(Exception):
    pass
