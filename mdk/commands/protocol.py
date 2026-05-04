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

MDK - Protocol switcher: toggle a Moodle instance between HTTP and HTTPS
- HTTPS via localhost.run (currnetly only option)
- HTTP uses http://<mdk-config-host>/<instanceName>
- Updates $CFG->wwwroot and $CFG->sslproxy
"""

import json
import logging
import os
import re
import signal
import subprocess
import time

from urllib.parse import urlparse, urlunparse
from typing import Union

from ..command import Command
from ..config import Conf
from ..tools import yesOrNo

_TUNNEL_META = '.mdk_protocol_tunnel.json'
_LOG_FILE = '.mdk_protocol_tunnel.log'

class ProtocolCommand(Command):
    _arguments = [
        (['mode'], {
            'choices': ['http', 'https', 'toggle'],
            'help': 'Target protocol or "toggle"',
        }),
        (['-f'], {
            'action': 'store_true',
            'dest': 'force',
            'help': 'Force without confirmation (dangerous)',
        }),
        (['--port'], {
            'type': int,
            'default': 80,
            'help': 'Local HTTP port your instance is served on (for tunnelling).',
        }),
        (['--show-log'], {
            'action': 'store_true',
            'help': 'Stream tunnel output in this terminal and write it to a log file',
        }),
        (['name'], {
            'default': None,
            'help': 'Name of the instance to work on',
            'metavar': 'name',
            'nargs': '?'
        }),
    ]
    _description = 'Switch (http <-> https) by launching a tunnel using localhost.run and rewriting $CFG->wwwroot and $CFG->sslproxy in config.php'

    def run(self, args):
        M = self.Wp.resolve(args.name)
        if not M:
            raise Exception('No instance to work on.')

        instpath = M.get('path')
        configphp = _find_config_php(instpath)

        src = _read(configphp)
        wwwroot = _extract_wwwroot(src)
        if not wwwroot:
            raise Exception(f'Could not locate $CFG->wwwroot in {configphp}')

        cur_scheme = (urlparse(wwwroot).scheme or 'http').lower()
        target = {'toggle': ('https' if cur_scheme == 'http' else 'http')}.get(args.mode, args.mode)

        # Decide new URL + sslproxy
        if target == 'https':
            label = M.get('identifier')
            public_url, proc = _ensure_localhost_run(args.port, instpath, label, args.show_log)
            new_wwwroot = _apply_base_to_path(public_url, urlparse(wwwroot).path)
            sslproxy = True
            _persist_tunnel_info(instpath, proc, kind='localhost.run')
        else:
            # HTTP: stop tunnels and build http://<host>/<instanceName>
            _stop_localhost_run_if_any(instpath)
            _delete_tunnel_meta(instpath)

            instname = (args.name or M.get('identifier')) or 'moodle'
            C = Conf()
            base_host = (C.get('host') or C.get('webserver.host') or '127.0.0.1')
            new_wwwroot = _compose_url('http', base_host, f'/{instname}')
            sslproxy = False

        if new_wwwroot == wwwroot and not args.force:
            logging.info('wwwroot unchanged (%s). Use -f to rewrite anyway.', new_wwwroot)
            return

        # Confirm
        if not args.force:
            if not yesOrNo(f'Change URL:\n  {wwwroot}\n→ {new_wwwroot}\nProceed?'):
                logging.info('Aborting...')
                return

        # Write back atomically: wwwroot + sslproxy
        newsrc = _set_sslproxy(_rewrite_wwwroot(src, new_wwwroot), sslproxy)
        _atomic_write(configphp, newsrc)

        logging.info('Protocol switched to %s', target.upper())
        logging.info('New $CFG->wwwroot: %s', new_wwwroot)
        logging.info('$CFG->sslproxy set to %s', 'true' if sslproxy else 'false')


# ------------ file helpers ------------

def _find_config_php(instpath: str) -> str:
    guess = os.path.join(instpath, 'config.php')
    if os.path.isfile(guess):
        return guess
    raise Exception('config.php not found under %s' % instpath)

def _read(path: str) -> str:
    return open(path, 'r', encoding='utf-8', errors='ignore').read()

def _atomic_write(path: str, content: str) -> None:
    """Write file atomically to avoid torn writes."""
    tmp = f"{path}.tmp.mdk"
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ------------ config.php mutation ------------

def _extract_wwwroot(src: str) -> Union[str, None]:
    m = re.search(r"""\$CFG->wwwroot\s*=\s*(['"])(.*?)\1\s*;""", src, re.I | re.S)
    return m.group(2) if m else None

def _rewrite_wwwroot(src: str, new_url: str) -> str:
    def repl(m):
        q = m.group(1)
        return f"$CFG->wwwroot = {q}{new_url}{q};"
    return re.sub(r"""\$CFG->wwwroot\s*=\s*(['"])(.*?)\1\s*;""", repl, src, flags=re.I | re.S)

def _set_sslproxy(src: str, enabled: bool) -> str:
    patt = re.compile(r"""\$CFG->sslproxy\s*=\s*(true|false)\s*;""", re.I)
    if patt.search(src):
        return patt.sub(f"$CFG->sslproxy = {'true' if enabled else 'false'};", src)
    www_patt = re.compile(r"""(\$CFG->wwwroot\s*=\s*['"].*?['"]\s*;)""", re.I | re.S)
    if www_patt.search(src):
        return www_patt.sub(rf"\1\n$CFG->sslproxy = {'true' if enabled else 'false'};", src, count=1)
    return src.rstrip() + f"\n$CFG->sslproxy = {'true' if enabled else 'false'};\n"


# ------------ URL helpers ------------

def _compose_url(scheme: str, host: str, path: str) -> str:
    return urlunparse((scheme, host, path or '/', '', '', ''))

def _apply_base_to_path(base: str, path: str) -> str:
    p = urlparse(base)
    return urlunparse((p.scheme, p.netloc, path or '/', '', '', ''))


# ------------ tunnel metadata ------------

def _tunnel_meta_path(instpath: str) -> str:
    """
    Return the absolute path to the metadata file used to remember the last
    tunnel we spawned for this instance.

    We persist a tiny JSON blob alongside the Moodle codebase (under `instpath`):
        {
          "pid": <int>,         # OS process id of the tunnel process we spawned
          "kind": "localhost.run" # which provider created the tunnel
        }

    Why this exists:
      - When switching back to HTTP, or switching providers, we need to cleanly
        stop any *previous* tunnel we started. To do that reliably across runs,
        we remember the PID and provider.

    Notes:
      - This file is overwritten each time a new tunnel is created.
      - If the process dies or is killed externally, the pid may be stale; our
        stop routine tolerates errors and simply removes the file.
    """
    return os.path.join(instpath, _TUNNEL_META)


def _persist_tunnel_info(instpath: str, proc: subprocess.Popen, kind: Union[str, None] = None) -> None:
    """
    Write the current tunnel's PID and provider 'kind' to the metadata file.

    Called right after a tunnel has been successfully started (we have a
    subprocess.Popen object and a public URL). This enables later cleanup.

    Parameters:
      instpath:  path to the Moodle instance root (where we store the file)
      proc:      the Popen object returned by the tunnel launcher
      kind:      'localhost.run' (used to selectively stop)
                 If None, the stop routine will match any kind.

    Failure handling:
      - Any exception here is ignored — not fatal for the main flow — but it
        means we may not be able to auto-stop the tunnel later.
    """
    try:
        with open(_tunnel_meta_path(instpath), 'w', encoding='utf-8') as f:
            json.dump({'pid': proc.pid, 'kind': kind}, f)
    except Exception:
        # Non-fatal: if persisting fails, we just won't be able to auto-stop.
        pass


def _delete_tunnel_meta(instpath: str) -> None:
    """
    Remove the metadata file unconditionally.

    Use this when:
      - Tearing down tunnels (HTTP mode), after we have attempted to stop them.
      - Resetting state before creating a new tunnel/provider.

    Safe to call even if the file does not exist. Any errors are ignored.
    """
    try:
        os.remove(_tunnel_meta_path(instpath))
    except Exception:
        pass


# ------------ tunnel management: localhost.run ------------

def _stop_localhost_run_if_any(instpath: str) -> None:
    _stop_tunnel_by_kind(instpath, 'localhost.run')

def _ensure_localhost_run(local_port: int, instpath: str, label: str, show_log: bool):
    """
    Start a localhost.run reverse SSH tunnel headlessly.
    Prefer JSON lines if present; fallback to regex that matches *.lhr.life
    """
    ssh_cmd = [
        'ssh',
        '-R',
        f'80:localhost:{local_port}',
        'localhost.run',
        '--',
        '--output',
        'json'  # structured output if supported
    ]
    proc = subprocess.Popen(
        ssh_cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        # text=True,
        universal_newlines=True,
        bufsize=1
    )

    # Accept e.g. https://44699e2cafddde.lhr.life
    url_re = re.compile(
        r'https:\/\/[a-z0-9]+\.1hr\.life\b',
        re.IGNORECASE
    )

    def emit(line: str):
        line = _to_str(line)
        with open(_log_path(instpath), 'a', encoding='utf-8', errors='ignore') as lf:
            lf.write(line)
        if show_log:
            print(f"[localhost.run] {line}", end='')

    def _to_str(s):
        # robust across 3.6/3.12: convert bytes -> str
        return s.decode('utf-8', 'ignore') if isinstance(s, (bytes, bytearray)) else s

    public_url = None
    t0 = time.time()
    timeout_sec = 25

    while time.time() - t0 < timeout_sec:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            time.sleep(0.05)
            continue

        line = _to_str(line)
        emit(line)

        # JSON-first path (some servers emit structured events)
        if line.lstrip().startswith('{'):
            try:
                evt = json.loads(line)
                host = evt.get('address') or evt.get('listen_host')
                if host:
                    scheme = 'https' if evt.get('tls_termination', True) else 'http'
                    public_url = f"{scheme}://{host}"
                    break
                msg = evt.get('message') or ''
                m = url_re.search(msg)
                if m:
                    public_url = m.group(0)
                    break
                for key in ('url', 'public_url', 'domain'):
                    val = evt.get(key)
                    if isinstance(val, str) and val.startswith('http'):
                        public_url = val
                        break
                if public_url:
                    break
            except json.JSONDecodeError:
                pass

        # Plaintext fallback
        m = url_re.search(line)
        if m:
            public_url = m.group(0)
            break

    if not public_url:
        try:
            proc.terminate()
        except Exception:
            pass
        raise Exception(f"Failed to detect localhost.run URL. See log: {_log_path(instpath)}")

    logging.info('localhost.run tunnel up for %s → %s', label, public_url)
    return public_url, proc

# ------------ shared tunnel stop / log paths ------------


def _stop_tunnel_by_kind(instpath: str, kind_expected: Union[str, None]) -> None:
    """
    Best-effort stop of a previously-started tunnel process recorded in metadata.

    Reads <instpath>/.mdk_protocol_tunnel.json for:
      - pid:  the process id to signal
      - kind: the provider that created it (current only 'localhost.run')

    Behavior:
      - If 'kind_expected' is None, any recorded tunnel is eligible to stop.
      - If 'kind_expected' is provided, only stop when it matches the recorded 'kind'.

    Important:
      - This only stops tunnels we spawned in this command (because we record
        their PID). If a user started a separate manual tunnel, we won't touch it.
      - We do not delete the metadata file here; higher-level callers decide
        whether to keep or remove it (e.g., HTTP mode deletes it).
    """
    meta = _tunnel_meta_path(instpath)
    if not os.path.isfile(meta):
        return
    try:
        with open(meta, 'r', encoding='utf-8') as f:
            data = json.load(f)
        pid = int(data.get('pid', 0))
        kind = data.get('kind')
        if pid > 0 and (kind == kind_expected or kind_expected is None):
            os.kill(pid, signal.SIGTERM)  # polite stop; tunnels should exit
            time.sleep(0.4)               # brief grace period
    except Exception:
        # Non-fatal: metadata may be stale or PID already gone.
        pass

def _log_path(instpath: str) -> str:
    return os.path.join(instpath, _LOG_FILE)
