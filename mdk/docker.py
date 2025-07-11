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

from mdk.tools import process


def create_docker_network(name: str) -> bool:
    """Create a Docker network with the given name."""
    r, _, _ = process(['docker', 'network', 'create', name])
    return r == 0


def docker_container_exists(name: str) -> bool:
    """Check if a Docker container exists."""
    r, _, _ = process(['docker', 'inspect', '--format', '{{.Id}}', name])
    return r == 0


def docker_network_exists(name: str) -> bool:
    """Check if a Docker network exists."""
    r, _, _ = process(['docker', 'network', 'inspect', name])
    return r == 0


def is_docker_container_running(name: str) -> bool:
    """Check if a Docker container is running."""
    r, _, _ = process(['docker', 'top', name])
    return r == 0


def ensure_docker_network_exists(name: str):
    """Ensure that a Docker network exists, creating it if necessary."""
    if docker_network_exists(name):
        return
    if not create_docker_network(name):
        raise Exception(f'Could not create the Docker network "{name}".')
