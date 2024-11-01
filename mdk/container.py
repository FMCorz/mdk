import abc
import os
from pathlib import Path
import shutil
from typing import Dict, List, Optional
from mdk.config import Conf

from mdk.tools import get_absolute_path, mkdir, process

C = Conf()


def is_docker_container_running(name: str) -> bool:
    """Check if a Docker container is running."""
    r, _, _ = process(['docker', 'top', name])
    return r == 0


class Container(abc.ABC):
    """Interface to abstract env and commands inside a container."""

    @abc.abstractmethod
    def chmod(self, path: Path, mode: int) -> None:
        pass

    @abc.abstractmethod
    def exists(self, path: Path) -> bool:
        pass

    @abc.abstractmethod
    def exec(self, command: List[str], **kwargs):
        pass

    @abc.abstractmethod
    def isdir(self, path: Path) -> bool:
        pass

    @abc.abstractmethod
    def mkdir(self, path: Path, mode: int) -> None:
        pass

    @property
    @abc.abstractmethod
    def path(self) -> Path:
        pass

    @abc.abstractmethod
    def rmtree(self, path: Path) -> None:
        pass

    @property
    @abc.abstractmethod
    def dataroot(self) -> Path:
        pass

    @property
    @abc.abstractmethod
    def behat_dataroot(self) -> Path:
        pass

    @property
    @abc.abstractmethod
    def behat_faildumps(self) -> Optional[Path]:
        """Return the path to the fail dumps directory. I'm not convinced about this."""
        return None

    @property
    @abc.abstractmethod
    def behat_wwwroot(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def phpunit_dataroot(self) -> Path:
        pass


class HostContainer(Container):
    """Pretends to be a container but is the host machine."""
    _identifier: Optional[str]
    _path: Path
    _dataroot: Optional[Path]
    _binaries: Dict[str, str]

    def __init__(
        self, *, path: Path, identifier: Optional[str] = None, dataroot: Optional[Path] = None, binaries: Dict[str, str] = None
    ):
        self._identifier = identifier
        self._path = path
        self._dataroot = dataroot
        self._binaries = binaries or {}

    def chmod(self, path: Path, mode: int) -> None:
        os.chmod(get_absolute_path(path, self.path), mode)

    def exists(self, path: Path) -> bool:
        return (get_absolute_path(path, self.path)).exists()

    def exec(self, command: List[str], **kwargs):
        bin = command[0]
        if bin in self._binaries:
            command[0] = self._binaries[bin]
        return process(command, cwd=self.path, **kwargs)

    def isdir(self, path: Path) -> bool:
        return (get_absolute_path(path, self.path)).is_dir()

    def mkdir(self, path: Path, mode: int) -> None:
        mkdir(get_absolute_path(path, self.path), mode)

    @property
    def path(self) -> Path:
        return self._path

    def rmtree(self, path: Path) -> None:
        shutil.rmtree(get_absolute_path(path, self.path), True)

    @property
    def dataroot(self) -> Path:
        if not self._dataroot:
            raise ValueError('Unknown dataroot.')
        return self._dataroot

    @property
    def behat_dataroot(self) -> Path:
        if not self._dataroot:
            raise ValueError('Cannot resolve behat dataroot without dataroot.')
        return self._dataroot.with_name(self._dataroot.name + '_behat')

    @property
    def behat_faildumps(self) -> Optional[Path]:
        return None

    @property
    def behat_wwwroot(self) -> str:
        if not self._identifier:
            raise ValueError('Instance identifier unknown.')
        wwwroot = '%s://%s/' % (C.get('scheme'), C.get('behat.host'))
        if C.get('path'):
            wwwroot = wwwroot + C.get('path') + '/'
        return wwwroot + self._identifier

    @property
    def phpunit_dataroot(self) -> Path:
        if not self._dataroot:
            raise ValueError('Cannot resolve PHPUnit dataroot without dataroot.')
        return self._dataroot.with_name(self._dataroot.name + '_phpu')


class DockerContainer(Container):
    """Docker container."""
    _name: str
    _hostpath: Path

    def __init__(self, *, hostpath: Path, name: str):
        self._name = name
        self._hostpath = hostpath

    def chmod(self, path: Path, mode: int) -> None:
        path = get_absolute_path(path, self.path)
        self.exec(['chmod', f'{mode:o}', path.as_posix()])

    def exists(self, path: Path) -> bool:
        r, _, _ = self.exec(['test', '-e', (get_absolute_path(path, self.path)).as_posix()])
        return r == 0

    def exec(self, command: List[str], **kwargs):
        # We surely will want to customise the user, but for simplicity at the moment all is done by root.
        hostcommand = ['docker', 'exec', '-w', self.path.as_posix(), '-u', '0:0', '-it', self._name, *command]
        return process(hostcommand, cwd=self._hostpath, **kwargs)

    def isdir(self, path: Path) -> bool:
        r, _, _ = self.exec(['test', '-d', get_absolute_path(path, self.path).as_posix()])
        return r == 0

    def mkdir(self, path: Path, mode: int) -> None:
        path = get_absolute_path(path, self.path)
        self.exec(['mkdir', '-p', path.as_posix()])
        self.chmod(path, mode)

    @property
    def path(self) -> Path:
        return Path('/var/www/html')

    def rmtree(self, path: Path) -> None:
        path = get_absolute_path(path, self.path)
        self.exec(['rm', '-r', path.as_posix()])

    @property
    def dataroot(self) -> Path:
        return Path('/var/www/moodledata')

    @property
    def behat_dataroot(self) -> Path:
        return Path('/var/www/behatdata')

    @property
    def behat_faildumps(self) -> Optional[Path]:
        return Path('/var/www/behatfaildumps')

    @property
    def behat_wwwroot(self) -> str:
        return f'http://{self._name}'

    @property
    def phpunit_dataroot(self) -> Path:
        return Path('/var/www/phpunitdata')
