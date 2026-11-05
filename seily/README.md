# Seily

Seily is a Mocktail-based project with a boat icon, a launcher, isolated data and
an automatic upstream runtime updater. The playable runtime is the official
Mocktail AppImage, not a separately compiled or modified Mocktail binary.
The source tree remains available for developing the fork independently.

On each launch Seily checks GitHub's latest Mocktail release. It verifies the
release's SHA-256 checksum before replacing its cached runtime. If the check or
download fails, the last cached runtime is used. Roblox's client is downloaded
separately by Mocktail. Seily does not update the source tree automatically.

Seily asks Mocktail for unlimited FPS and disables vsync. Actual FPS depends on
Roblox, drivers and hardware; tearing and increased heat/power use are possible.
If you prefer the defaults, remove those two environment settings in seily.py.
The runtime and isolated configuration/data are under ~/.local/share/seily/.

## Install

On x86-64 Linux, install Python 3, PyGObject, GTK 4, and an AppImage runtime
(including FUSE where needed). On Fedora, `sudo dnf install python3-gobject gtk4`
installs the UI dependencies. From the project root, run:

```sh
bash seily/install.sh
```

Keep the source directory in place: the app-menu entry runs its `setup.py`.
On first launch Seily downloads the official Mocktail AppImage. Seily's launcher
and source are not auto-updated; only the Mocktail runtime is. Roblox's in-game
graphics settings control visual quality; the launcher does not claim to set
texture quality. Performance settings are requests, not guaranteed FPS gains.

Upstream: https://github.com/komaruworld/mocktail (Apache-2.0).
