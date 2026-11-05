# Seily

Seily is a Mocktail-based project with a boat icon, a launcher, isolated data and
an automatic upstream runtime updater. The playable runtime is the official
Mocktail AppImage, not a separately compiled or modified Mocktail binary.
The source tree remains available for developing the fork independently.

On each launch Seily checks GitHub's latest Mocktail release. It verifies the
release's SHA-256 checksum before replacing its cached runtime. If the check or
download fails, the last cached runtime is used. Roblox's client is downloaded
separately by Mocktail. Seily does not update the source tree automatically.

The setup window lets you choose an FPS limit and vsync mode. Actual FPS depends
on Roblox, drivers and hardware; disabling vsync can cause tearing and uncapped
FPS can increase heat and power use.
The runtime and isolated configuration/data are under ~/.local/share/seily/.

## Install

On x86-64 Linux, install Python 3, PyGObject, GTK 4, and an AppImage runtime
(including FUSE where needed). On Fedora, `sudo dnf install python3-gobject gtk4`
installs the UI dependencies. Clone your own copy and install:

On Arch Linux, install them with `sudo pacman -S --needed git python python-gobject gtk4 fuse2`.

```sh
git clone https://github.com/ash262049-png/seily.git
cd seily
bash seily/install.sh
```

Keep the source directory in place: the app-menu entry runs its `setup.py`.
Open **Seily** to play directly, or **Seily Settings** to change and save presets.
On first launch Seily downloads the official Mocktail AppImage. Seily's launcher
and source are not auto-updated; only the Mocktail runtime is. Roblox's in-game
graphics settings control visual quality. Seily also offers an experimental
texture mip-bias override; Roblox may ignore it. Performance settings are
requests, not guaranteed FPS gains.

For the verified Mocktail 1.0.5 AppImage, Seily uses a build-specific audio
profile to expose host microphones. Its first launch extracts a runtime copy
(roughly 600 MB). Other runtime versions use their upstream profiles.

Upstream: https://github.com/komaruworld/mocktail (Apache-2.0).
