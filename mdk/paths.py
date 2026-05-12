#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Moodle component paths resolver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

PLUGINTYPES_PATH = Dict[str, Path]
SUBSYSTEMS_PATH = Dict[str, Union[Path, None]]


class ComponentResolver():
    """Resolves component paths from a Moodle instance root folder."""

    def __init__(self, root: Path, *, admin: str = 'admin') -> None:
        self._root = root.resolve()
        self._admin = admin or 'admin'
        self._plugintypes: PLUGINTYPES_PATH = {}
        self._subsystems: SUBSYSTEMS_PATH = {}
        self._subplugintypes: PLUGINTYPES_PATH = {}
        self._components_loaded = False
        self._subplugins_loaded = False

    def _path_from_json_literal(self, raw: Union[str, None]) -> Optional[Path]:
        if raw is None:
            return None
        s = raw.strip().strip('/')
        return self._rewrite_path_for_admin_root(Path(s)) if s else None

    def _rewrite_path_for_admin_root(self, path: Optional[Path]) -> Optional[Path]:
        if self._admin == 'admin':
            return path
        elif path is None:
            return None

        adminroot = Path(self._admin)
        if path == Path('admin'):
            return adminroot
        elif path.is_relative_to('public/admin'):
            return adminroot / path.relative_to('public/admin')
        elif path.is_relative_to('admin'):
            return adminroot / path.relative_to('admin')

        return path

    def _load_components(self) -> None:
        if self._components_loaded:
            return
        self._components_loaded = True

        componentsjson = self._root / Path('lib/components.json')
        if not componentsjson.is_file():
            raise ValueError('Missing lib/components.json under Moodle dirroot')

        with open(componentsjson, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError('Invalid lib/components.json structure')

        self._plugintypes = {}
        for t, p in data['plugintypes'].items():
            self._plugintypes[str(t)] = self._path_from_json_literal(p)

        self._subsystems = {}
        for s, p in data['subsystems'].items():
            self._subsystems[str(s)] = self._path_from_json_literal(p)

    def _load_subplugins(self) -> None:
        if self._subplugins_loaded:
            return

        self._subplugintypes = {}
        self._subplugins_loaded = True
        self._load_components()

        for plugintype, relpath in list(self._plugintypes.items()):
            typeroot = self._root / relpath
            for plugindir in typeroot.iterdir():
                if not plugindir.is_dir():
                    continue
                self._load_subplugintypes_from_plugin(typeroot / plugindir)

    def _load_subplugintypes_from_plugin(self, pluginpath: Path) -> List[str]:
        file = pluginpath / 'db/subplugins.json'
        if not file.is_file():
            return []

        with open(file, 'r', encoding='utf-8') as f:
            subplugins = json.load(f)
        if not isinstance(subplugins, dict):
            return []

        if 'subplugintypes' in subplugins:
            for subplugin, relpath in subplugins['subplugintypes'].items():
                self._subplugintypes[subplugin] = pluginpath.relative_to(self._root) / self._path_from_json_literal(relpath)

        elif 'plugintypes' in subplugins:
            inpublic = pluginpath.is_relative_to(self._root / 'public')
            for subplugin, relpath in subplugins['plugintypes'].items():
                relpath = (Path('public') if inpublic else Path('')) / self._path_from_json_literal(relpath)
                self._subplugintypes[subplugin] = relpath

    def get_component_directory(self, token: str) -> Union[Path, None]:
        ctype, cname = self.normalise_component(token)

        if ctype == 'core':
            return self._root / (Path('lib') if not cname else self.get_subsystem_directory(cname))

        relroot = None
        if ctype in self.core_plugintypes:
            relroot = self.core_plugintypes[ctype]
        elif ctype in self.plugintypes:
            relroot = self.plugintypes[ctype]

        if not relroot:
            return None

        return self._root / relroot / (cname if cname else Path(''))

    def get_plugintype_directory(self, plugintype: str) -> Union[Path, None]:
        return self.plugintypes.get(plugintype)

    def get_subsystem_directory(self, subsystem: str) -> Union[Path, None]:
        return self.subsystems.get(subsystem)

    def normalise_component(self, token: str) -> Tuple[str, Union[str, None]]:
        """
        Normalises a component.

        This almost follows the same logic as core, except that components are not normalised
        to `mod` when they are not prefixed. Instead the plugintype, or subsystem, is returned.
        """

        t = token.strip().lower()
        if t in ('moodle', 'core'):
            return ('core', None)

        # Assume subsystem when no underscore in the token. No fallback on `mod/` like core.
        if '_' not in t:
            if t in self.subsystems:
                return ('core', t)
            elif t in self.plugintypes:
                return (t, None)
            raise ValueError(f'Unknown component: {token}')

        ctype, cname = t.split('_', 1)
        if ctype == 'moodle':
            ctype = 'core'

        return (ctype, cname)

    def plugintype_prefixes(self) -> List[str]:
        self._load_components()
        self._load_subplugins()
        return sorted(self._plugintypes.keys(), key=lambda s: (-len(s), s))

    @property
    def core_plugintypes(self) -> PLUGINTYPES_PATH:
        self._load_components()
        return self._plugintypes

    @property
    def plugintypes(self) -> PLUGINTYPES_PATH:
        return self.subplugintypes | self.core_plugintypes

    @property
    def subplugintypes(self) -> PLUGINTYPES_PATH:
        self._load_subplugins()
        return self._subplugintypes

    @property
    def subsystems(self) -> SUBSYSTEMS_PATH:
        self._load_components()
        return self._subsystems


def get_file_path_from_classname(classname: str, resolver: ComponentResolver) -> Path:
    """Resolve path to a PHP class file."""
    classname = classname.strip().strip('\\')

    component = None
    remainder = None
    if '\\' in classname:
        component, remainder = classname.split('\\', 1)
    elif classname.count('_') > 1:
        parts = classname.split('_', 2)
        component = '_'.join(parts[0:2])
        remainder = parts[2]
    else:
        raise ValueError(f'Invalid class name: {classname}')

    candidates = []
    if '\\' in classname:
        candidates.append(f'classes/{remainder.replace('\\', '/')}.php')
    else:
        candidates.append(f'classes/{remainder}.php')
        candidates.append(f'{remainder}.php')

    rootdir = resolver.get_component_directory(component)
    if not rootdir:
        raise ValueError(f'Could not resolve component directory for: {component}')

    # Attempt to resolve to a real file.
    for candidate in candidates:
        path = rootdir / candidate
        if path.exists():
            return path

    # Fallback on recommended path.
    return rootdir / candidates[0]