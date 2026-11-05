#!/usr/bin/env python3
"""Seily launcher: update and start the upstream Mocktail runtime."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request

HOME = Path.home()
ROOT = HOME / '.local/share/seily'
RUNTIME = ROOT / 'Mocktail.AppImage'
API = 'https://api.github.com/repos/komaruworld/mocktail/releases/latest'
HEADERS = {'User-Agent': 'Seily-launcher', 'Accept': 'application/vnd.github+json'}


def update():
    with urllib.request.urlopen(urllib.request.Request(API, headers=HEADERS), timeout=8) as response:
        release = json.load(response)
    asset = next(a for a in release['assets'] if a['name'].endswith('-x86_64.AppImage'))
    digest = asset.get('digest', '')
    if not digest.startswith('sha256:') or len(digest) != 71:
        raise ValueError('upstream did not publish a SHA-256 checksum')
    expected = digest[7:]
    if RUNTIME.exists():
        with RUNTIME.open('rb') as f:
            if hashlib.file_digest(f, 'sha256').hexdigest() == expected:
                return
    url = asset['browser_download_url']
    if not url.startswith('https://github.com/komaruworld/mocktail/releases/download/'):
        raise ValueError('unexpected release download URL')
    ROOT.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=ROOT, prefix='.download-', delete=False) as out:
            temp_name = out.name
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
                shutil.copyfileobj(response, out)
        with open(temp_name, 'rb') as f:
            if hashlib.file_digest(f, 'sha256').hexdigest() != expected:
                raise ValueError('download checksum mismatch')
        os.chmod(temp_name, 0o755)
        os.replace(temp_name, RUNTIME)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def prepare_runtime():
    try:
        update()
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as error:
        print(f'Seily: update unavailable: {error}', file=sys.stderr)
    if not RUNTIME.is_file():
        raise RuntimeError('No runtime is available. Connect to the internet and try again.')


def runtime_environment(settings=None):
    settings = settings or {}
    env = os.environ.copy()
    # Keep all Mocktail state separate from both the Flatpak and native installs.
    for name, suffix in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                         ('XDG_CACHE_HOME', 'cache'), ('XDG_STATE_HOME', 'state')]:
        path = ROOT / suffix
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    fps = settings.get('fps', 'unlimited')
    # Mocktail's "unlimited" maps to 240; request a higher explicit target.
    env['MOCKTAIL_FRAME_RATE_LIMIT'] = '9999' if fps == 'unlimited' else fps
    env['MOCKTAIL_VSYNC'] = settings.get('vsync', 'off')
    env['MOCKTAIL_GRAPHICS_BACKEND'] = settings.get('backend', 'direct-vulkan')
    env['MOCKTAIL_MULTITHREADED_RENDERING'] = '1' if settings.get('multithreaded', False) else '0'
    texture = settings.get('texture', 'default')
    if texture in ('1', '2'):
        try:
            overrides = json.loads(env.get('MOCKTAIL_CLIENT_SETTINGS_OVERRIDES_JSON', '{}'))
            if not isinstance(overrides, dict):
                raise ValueError('client settings overrides must be a JSON object')
        except json.JSONDecodeError as error:
            raise ValueError('client settings overrides contain invalid JSON') from error
        overrides['FIntRenderTextureMipBias'] = texture
        env['MOCKTAIL_CLIENT_SETTINGS_OVERRIDES_JSON'] = json.dumps(overrides)
        # Mocktail's throughput policy chooses bias 2 only for quality "1";
        # match it so that it doesn't reject the explicit override as a conflict.
        env['MOCKTAIL_GRAPHICS_QUALITY'] = '1' if texture == '2' else 'auto'
    return env


def main():
    try:
        prepare_runtime()
    except RuntimeError as error:
        print(f'Seily: {error}', file=sys.stderr)
        return 1
    env = runtime_environment()
    os.execve(str(RUNTIME), [str(RUNTIME), *sys.argv[1:]], env)


if __name__ == '__main__':
    sys.exit(main())
