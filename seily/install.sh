#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" || {
  echo 'Python GObject and GTK 4 are required (on Fedora: sudo dnf install python3-gobject gtk4).' >&2
  exit 1
}
mkdir -p "$data/applications" "$data/icons/hicolor/512x512/apps"
install -m 644 "$root/seily.png" "$data/icons/hicolor/512x512/apps/seily.png"
ROOT="$root" DATA_DIR="$data" python3 - <<'PY'
import os
from pathlib import Path
root = os.environ['ROOT']
data = Path(os.environ['DATA_DIR'])
# Desktop entries have their own quoting rules; escape special characters.
entry = str(Path(root) / 'setup.py').replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
desktop = f'''[Desktop Entry]
Type=Application
Name=Seily
GenericName=Roblox Player
Comment=Play Roblox on Linux with Seily
Exec=python3 "{entry}" --play
Icon={data / 'icons/hicolor/512x512/apps/seily.png'}
Categories=Game;
Terminal=false
StartupNotify=true
'''
(data / 'applications/seily.desktop').write_text(desktop)
settings = desktop.replace('Name=Seily\n', 'Name=Seily Settings\n').replace(
    'Comment=Play Roblox on Linux with Seily', 'Comment=Configure Seily graphics and performance').replace(
    f'Exec=python3 "{entry}" --play', f'Exec=python3 "{entry}"')
(data / 'applications/seily-settings.desktop').write_text(settings)
PY
if command -v update-desktop-database >/dev/null; then
  update-desktop-database "$data/applications"
fi
echo "Seily installed. Keep this source folder in place, then open Seily from your app menu."
