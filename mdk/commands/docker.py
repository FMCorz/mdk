"""
Moodle Development Kit

Copyright (c) 2025 Frédéric Massart

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

import argparse
import json
import logging
import re
from pathlib import Path
import subprocess
from typing import Optional
from urllib.parse import urlencode

from mdk.command import Command
from mdk.docker import (docker_container_exists, ensure_docker_network_exists, get_local_docker_port, is_docker_container_running)
from mdk.moodle import Moodle
from mdk.tools import get_major_version_from_release, open_in_browser, process

logger = logging.getLogger(__name__)


class DockerCommand(Command):

    _description = "Manages container instances"

    def setup_args(self, parser):

        parent = argparse.ArgumentParser(add_help=False)
        parent.add_argument('instance', nargs='?', help='name of the instance')

        subparser = parser.add_subparsers(dest='action', metavar='action', help='the action to perform', required=True)

        # Up, down, rm, stop.
        upparser = subparser.add_parser('up', parents=[parent], help='create and start Moodle in a container')
        upparser.add_argument('-p', '--port', metavar='port', type=int, help='the local port to use')
        upparser.add_argument(
            '-v',
            '--php',
            metavar='version',
            dest='phpversion',
            choices=['7.4', '8.0', '8.1', '8.2', '8.3', '8.4'],
            help='the PHP version to use',
        )
        upparser.add_argument('-N', '--no-create', action='store_true', help='do not create the container if it does not exist')
        upparser.add_argument('--xdebug', action='store_true', help='enable the Xdebug extension in the container')

        downparser = subparser.add_parser('down', parents=[parent], help='stop and remove the Moodle container')
        rmparser = subparser.add_parser('rm', parents=[parent], help='remove the Moodle container')
        stopparser = subparser.add_parser('stop', parents=[parent], help='stop the Moodle container')
        logsparser = subparser.add_parser('logs', parents=[parent], help='explore the logs of the container')
        logsparser.add_argument(
            '-f',
            '--follow',
            action='store_true',
            help='follow the logs',
        )

        # Database.
        dbparser = subparser.add_parser('db', help='manage the database containers')
        subdbparser = dbparser.add_subparsers(
            dest='subaction',
            metavar='action',
            help='the database action to perform',
            required=True,
        )

        updbparser = subdbparser.add_parser('up', help='create and start the database container')
        engines = [k for k, v in self.C.get('db').items() if type(v) is dict and v.get('dockername')]
        updbparser.add_argument('name', help='the name of the database profile', choices=engines)

        # Adminer.
        adminerparser = subparser.add_parser('adminer', help='manage the Adminer container')
        subadminerparser = adminerparser.add_subparsers(
            dest='subaction',
            metavar='action',
            help='the Adminer action to perform',
            required=True,
        )
        upadminerparser = subadminerparser.add_parser('up', parents=[parent], help='create and start the Adminer container')
        upadminerparser.add_argument(
            '-o',
            '--open',
            action='store_true',
            help='open the Adminer URL in the browser',
        )
        upadminerparser.add_argument(
            '-t',
            '--table',
            help='the table to open (prefix optional)',
        )
        downadminerparser = subadminerparser.add_parser('down', help='stop and remove the container')
        openadminerparser = subadminerparser.add_parser('open', parents=[parent], help='open the Adminer URL in the browser')
        openadminerparser.add_argument(
            '-t',
            '--table',
            help='the table to open (prefix optional)',
        )

        # Selenium.
        seleniumparser = subparser.add_parser('selenium', help='manage the Selenium container')
        subseleniumparser = seleniumparser.add_subparsers(
            dest='subaction',
            metavar='action',
            help='the Selenium action to perform',
            required=True,
        )
        upseleniumparser = subseleniumparser.add_parser('up', parents=[parent], help='create and start the Selenium container')
        upseleniumparser.add_argument(
            '-t',
            '--variant',
            metavar='variant',
            choices=['firefox', 'chrome', 'chromium'],
            default='firefox',
            help='the browser variant to use'
        )
        downseleniumparser = subseleniumparser.add_parser('down', parents=[parent], help='stop and remove the container')
        downseleniumparser.add_argument(
            '-t',
            '--variant',
            metavar='variant',
            choices=['firefox', 'chrome', 'chromium'],
            default='firefox',
            help='the browser variant to use'
        )

    def run(self, args):
        fnname = f'run_{args.action}' if 'subaction' not in args else f'run_{args.action}_{args.subaction}'
        fn = getattr(self, fnname, None)
        if not fn:
            raise NotImplementedError(f'Method "{fnname}" is not implemented.')
        fn(args)

    def run_up(self, args: argparse.Namespace):
        M = self.Wp.resolve(args.instance, raise_exception=True)
        dockername = M.identifier
        dockernet = self.C.get('docker.network')

        if is_docker_container_running(dockername):
            logging.info(f'The container "{dockername}" is already running.')
            return

        elif docker_container_exists(dockername):
            logging.info(f'Starting existing container "{dockername}".')
            process(['docker', 'start', dockername])
            return

        elif args.no_create:
            raise Exception(f'The container "{dockername}" does not exist, creation not allowed.')

        port = args.port
        if not port and M.isInstalled():
            portmatch = re.search(r'^https?://.*:(\d+)(/.*)?$', M.get('wwwroot'))
            port = int(portmatch.group(1)) if portmatch else 8800

        if is_port_in_use(port):
            raise Exception(f'The port {port} is already in use. Please choose another one.')

        phpversion = args.phpversion
        if not phpversion:
            logging.info('PHP version not specified, trying to guess from instance.')
            phpversion = guess_php_version(M)

        if not phpversion:
            raise Exception('The argument --php-version (-v) is required to create the container.')

        dataroot = self.Wp.getPath(M.identifier, 'data')
        behatfaildumps = self.Wp.getExtraDir(M.identifier, 'behat')

        ensure_docker_network_exists(dockernet)

        envvars = {
            'MDK_DOCKER_NAME': dockername,
        }
        if args.xdebug:
            envvars['PHP_EXTENSION_xdebug'] = '1'
            envvars['PHP_INI-xdebug.client_host'] = 'host.docker.internal'
            envvars['PHP_INI-xdebug.mode'] = 'develop,debug'
            envvars['PHP_INI-xdebug.start_with_request'] = 'yes'

        r, _, _ = process(
            [
                'docker',
                'run',
                '-d',
                '--name',
                dockername,
                '--network',
                dockernet,
                '--volume',
                f'{M.path}:/var/www/html',
                '--volume',
                f'{dataroot}:/var/www/moodledata',
                '--volume',
                f'{behatfaildumps}:/var/www/behatfaildumps',
                *[item for k, v in envvars.items() for item in ['-e', f'{k}={v}']],
                '-p',
                f'{port}:80',
                '--add-host',
                'host.docker.internal:host-gateway',
                f'moodlehq/moodle-php-apache:{phpversion}',
            ],
            stdout=None,
            stderr=None,
        )

        if r != 0:
            raise Exception('Failed to start the container.')

        logging.info(f'The container "{dockername}" has been started on port {port}.')

    def run_down(self, args: argparse.Namespace):
        M = self.Wp.resolve(args.instance, raise_exception=True)
        dockername = M.identifier
        if is_docker_container_running(dockername) and not self._stop(dockername):
            return
        self._rm(dockername)

    def run_logs(self, args: argparse.Namespace):
        M = self.Wp.resolve(args.instance, raise_exception=True)
        dockername = M.identifier

        if not is_docker_container_running(dockername):
            raise Exception(f'The container "{dockername}" is not running.')

        try:
            r, stdout, stderr = process(
                ['docker', 'logs', dockername] + (['-f'] if args.follow else []),
                stdout=subprocess.DEVNULL,
                stderr=None,
            )
        except KeyboardInterrupt:
            pass

    def run_rm(self, args: argparse.Namespace):
        M = self.Wp.resolve(args.instance, raise_exception=True)
        dockername = M.identifier
        if is_docker_container_running(dockername):
            raise Exception(f'The container "{dockername}" is running. Please stop, or use command down.')
        elif not docker_container_exists(dockername):
            logging.info(f'The container "{dockername}" does not exist, nothing to remove.')
            return
        self._rm(dockername)

    def run_stop(self, args: argparse.Namespace):
        M = self.Wp.resolve(args.instance, raise_exception=True)
        dockername = M.identifier
        self._stop(dockername)

    def run_db_up(self, args: argparse.Namespace):
        dbprofile = self.C.get('db')[args.name]
        dockernet = self.C.get('docker.network')
        dockername = dbprofile.get('dockername')

        if not dockername:
            raise ValueError('Invalid database profile, it must a docker profile and declare `dockername`.')
        elif dbprofile['engine'] != 'pgsql':
            raise NotImplementedError(f'The database engine "{dbprofile["engine"]}" is not supported by this command.')

        if is_docker_container_running(dockername):
            logging.info(f'The database container "{dockername}" is already running.')
            return

        elif docker_container_exists(dockername):
            logging.info(f'Starting existing database container "{dockername}".')
            process(['docker', 'start', dockername])
            return

        ensure_docker_network_exists(dockernet)

        # Prepare a local folder to store the data.
        pgdata = Path(self.C.get('dirs.mdk'), 'pgsqldata', args.name).expanduser().absolute()
        if not pgdata.exists():
            logging.info(f'Creating PostgreSQL data directory at {pgdata}.')
            pgdata.mkdir(parents=True, exist_ok=True)
            pgdata.chmod(0o777)

        # The mountpoint changes with Postgres 18
        dockerimage = dbprofile.get('dockerimage', 'postgres:latest')
        r, volumesraw, _ = process(['docker', 'image', 'inspect', '--format', '{{json .Config.Volumes}}', dockerimage])
        if r != 0:
            process(['docker', 'pull', dockerimage], stdout=None, stderr=None)
            r, volumesraw, _ = process(['docker', 'image', 'inspect', '--format', '{{json .Config.Volumes}}', dockerimage])
        if r != 0:
            raise Exception(f'Could not inspect the Docker image "{dockerimage}".')
        volumes = json.loads(volumesraw) or {}
        mountpoint = '/var/lib/postgresql' if '/var/lib/postgresql' in volumes else '/var/lib/postgresql/data'

        r, _, _ = process(
            [
                'docker',
                'run',
                '-d',
                '--name',
                dockername,
                '--network',
                dockernet,
                '--volume',
                f'{pgdata}:{mountpoint}',
                '-e',
                f'MDK_DOCKER_NAME={dockername}',
                '-e',
                f'POSTGRES_PASSWORD={dbprofile["passwd"]}',
                dbprofile.get('dockerimage', 'postgres:latest'),
            ],
            stdout=None,
            stderr=None,
        )

        if r != 0:
            raise Exception('Failed to start the database container.')

        logging.info(f'The database container "{dockername}" has been started.')

    def run_adminer_up(self, args: argparse.Namespace):
        instance = self.Wp.resolve(args.instance)

        dockernet = self.C.get('docker.network')
        imagename = self.C.get('adminer.image')
        dockername = self.C.get('adminer.name')
        port = self.C.get('adminer.port')

        if not docker_container_exists(dockername):
            ensure_docker_network_exists(dockernet)

            r, _, _ = process(
                [
                    'docker',
                    'run',
                    '-d',
                    '--restart',
                    'unless-stopped',
                    '--name',
                    dockername,
                    '--network',
                    dockernet,
                    '-p',
                    f'{port}:8080',
                    '-e',
                    f'MDK_DOCKER_NAME={dockername}',
                    imagename,
                ],
                stdout=None,
                stderr=None,
            )

            if r != 0:
                raise Exception('Failed to start the container.')

            logging.info(f'The container "{dockername}" has been started.')

        elif not is_docker_container_running(dockername):
            logging.info(f'The container "{dockername}" already exists, starting...')
            r, _, _ = process(['docker', 'start', dockername], stdout=None, stderr=None)
            if r != 0:
                raise Exception('Failed to start the container.')

        else:
            logging.info(f'The container "{dockername}" is already running.')

        if args.open:
            adminer_open(self.C.get('adminer.port'), instance, args.table)

    def run_adminer_down(self, args: argparse.Namespace):
        self._stop(self.C.get('adminer.name'))
        self._rm(self.C.get('adminer.name'))

    def run_adminer_open(self, args: argparse.Namespace):
        if not is_docker_container_running(self.C.get('adminer.name')):
            raise Exception(f'The container is not running, see the up command.')
        instance = self.Wp.resolve(args.instance)
        adminer_open(self.C.get('adminer.port'), instance, args.table)

    def run_selenium_up(self, args: argparse.Namespace):
        instance = self.Wp.resolve(args.instance)

        dockernet = self.C.get('docker.network')
        imagename = f'selenium/standalone-{args.variant}:3'
        dockername = f'selenium-{args.variant}'

        if is_docker_container_running(dockername):
            logging.info(f'The Selenium container "{dockername}" is already running.')
            return

        elif docker_container_exists(dockername):
            raise Exception(f'The container "{dockername}" already exists. Please remove it first.')

        ensure_docker_network_exists(dockernet)

        r, _, _ = process(
            [
                'docker',
                'run',
                '--rm',  # Delete when stopped.
                '-d',
                '--name',
                dockername,
                '--network',
                dockernet,
            ] + ([
                '--volume',
                f'{instance.path}:/var/www/html',
            ] if instance else []) + [
                '-e',
                f'MDK_DOCKER_NAME={dockername}',
                imagename,
            ],
            stdout=None,
            stderr=None,
        )

        if r != 0:
            raise Exception('Failed to start the Selenium container.')

        logging.info(f'The Selenium container "{dockername}" has been started.')

    def run_selenium_down(self, args: argparse.Namespace):
        dockername = f'selenium-{args.variant}'
        self._stop(dockername)

    def _rm(self, name) -> bool:
        if not is_mdk_container(name):
            raise Exception(f'The container "{name}" does not appear to be managed by MDK, not removing it.')

        logging.info(f'Removing the container "{name}".')
        r, _, _ = process(['docker', 'rm', name], stdout=None, stderr=None)
        return r == 0

    def _stop(self, name) -> bool:
        if not is_docker_container_running(name):
            logging.info(f'The container "{name}" is not running.')
            return False

        r, _, _ = process(['docker', 'stop', name], stdout=None, stderr=None)
        return r == 0


def docker_get_container_env(name: str) -> dict:
    """Get the container env."""
    r, out, _ = process(['docker', 'inspect', '--format', '{{join .Config.Env "\\n"}}', name])
    if r != 0:
        raise Exception(f'Could not get the environment variables from the container "{name}".')

    envs = {}
    for line in out.splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        envs[key] = value

    return envs


def guess_php_version(M: Moodle) -> Optional[str]:
    envfile = Path(M.path) / Path('admin/environment.xml')
    if not envfile.exists():
        raise Exception('The environment file does not exist in the container.')

    phpversion = None
    version = get_major_version_from_release(M.get('release'))

    import xml.etree.ElementTree as ET
    tree = ET.parse(str(envfile))
    root = tree.getroot()

    lastmnode = root.findall('MOODLE')[-1] if root.findall('MOODLE') else None
    mnode = None
    for m in root.findall('MOODLE'):
        if m.attrib.get('version').strip() != version:
            continue

        mnode = m
        break

    mnode = mnode if mnode else lastmnode  # Not finding any means dev version, so use last version.
    if mnode:
        for php in mnode.findall('PHP'):
            if php.attrib.get('level') == 'required':
                phpversion = php.attrib.get('version').strip()
                break

    return '.'.join(phpversion.split('.')[:2]) if phpversion else None


def is_mdk_container(name: str) -> bool:
    """Check if the container is managed by MDK."""
    env = docker_get_container_env(name)
    return 'MDK_DOCKER_NAME' in env and env['MDK_DOCKER_NAME'] == name


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def adminer_open(port: int, M: Optional[Moodle], table: Optional[str] = None):
    url = f'http://localhost:{port:d}'
    qs = {}
    if M and M.get('dbtype') == 'pgsql':
        qs['pgsql'] = M.get('dbhost')
        qs['db'] = M.get('dbname')
        qs['username'] = M.get('dbuser')
        qs['password'] = M.get('dbpass')
        qs['ns'] = 'public'
        if table:
            if not table.startswith(M.get('prefix')):
                table = M.get('prefix') + table
            qs['select'] = table
        url += '?' + urlencode(qs)

    open_in_browser(url)
