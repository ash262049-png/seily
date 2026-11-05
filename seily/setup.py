#!/usr/bin/env python3
"""Seily's local setup and launch window."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib, Gtk

import seily

SETTINGS = seily.ROOT / 'settings.json'
PRESETS = {
    'Balanced': {'fps': 'display', 'vsync': 'auto', 'backend': 'direct-vulkan', 'multithreaded': False},
    'Maximum FPS': {'fps': 'unlimited', 'vsync': 'off', 'backend': 'direct-vulkan', 'multithreaded': True},
    'Roblox defaults': {'fps': '-1', 'vsync': 'auto', 'backend': 'direct-vulkan', 'multithreaded': False},
}
OPTIONS = {
    'fps': [('Roblox default', '-1'), ('Display refresh rate', 'display'), ('Unlimited', 'unlimited'), ('60 FPS', '60'), ('120 FPS', '120'), ('144 FPS', '144'), ('240 FPS', '240')],
    'vsync': [('Automatic', 'auto'), ('Off (may tear)', 'off'), ('On', 'on')],
    'backend': [('Vulkan (recommended)', 'direct-vulkan'), ('OpenGL', 'opengl'), ('System default', 'system'), ('ANGLE over Vulkan', 'angle-vulkan')],
}


def load_settings():
    defaults = PRESETS['Maximum FPS'].copy()
    try:
        data = json.loads(SETTINGS.read_text())
        if not isinstance(data, dict):
            return defaults
        for key, options in OPTIONS.items():
            if data.get(key) in [v for _, v in options]:
                defaults[key] = data[key]
        if isinstance(data.get('multithreaded'), bool):
            defaults['multithreaded'] = data['multithreaded']
    except (OSError, ValueError):
        pass
    return defaults


def save_settings(settings):
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile('w', dir=SETTINGS.parent, delete=False) as file:
            name = file.name
            json.dump(settings, file, indent=2)
            file.write('\n')
        os.replace(name, SETTINGS)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Seily')
        self.set_default_size(580, 670)
        self.set_icon_name('seily')
        scroll = Gtk.ScrolledWindow()
        self.set_child(scroll)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(24); box.set_margin_bottom(24)
        box.set_margin_start(28); box.set_margin_end(28)
        scroll.set_child(box)
        title = Gtk.Label(label='⛵  Seily')
        title.add_css_class('title-1')
        title.set_xalign(0)
        box.append(title)
        desc = Gtk.Label(label='Choose how you want to play, then launch Roblox.')
        desc.set_xalign(0); desc.set_wrap(True); desc.add_css_class('dim-label')
        box.append(desc)

        preset_label = Gtk.Label(label='Quick setup'); preset_label.set_xalign(0)
        preset_label.add_css_class('heading'); box.append(preset_label)
        buttons = Gtk.Box(spacing=8)
        for name in PRESETS:
            button = Gtk.Button(label=name)
            button.connect('clicked', self.apply_preset, name)
            button.set_hexpand(True); buttons.append(button)
        box.append(buttons)

        self.controls = {}
        for key, label in [('fps', 'Frame rate'), ('vsync', 'Vertical sync'), ('backend', 'Graphics renderer')]:
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            heading = Gtk.Label(label=label); heading.set_xalign(0); heading.add_css_class('heading')
            row.append(heading)
            dropdown = Gtk.DropDown.new_from_strings([name for name, _ in OPTIONS[key]])
            row.append(dropdown); self.controls[key] = dropdown; box.append(row)
        row = Gtk.Box(spacing=12)
        label = Gtk.Label(label='Multithreaded rendering'); label.set_xalign(0); label.set_hexpand(True)
        self.multi = Gtk.Switch(); row.append(label); row.append(self.multi); box.append(row)

        note = Gtk.Label(label='Texture quality is controlled by Roblox: in a game, open Settings → Graphics Mode → Manual, then lower Graphics Quality for more FPS. Some experiences may ignore it.')
        note.set_wrap(True); note.set_xalign(0); note.add_css_class('dim-label'); box.append(note)
        self.status = Gtk.Label(label='Settings are saved when you press Play.')
        self.status.set_wrap(True); self.status.set_xalign(0); self.status.add_css_class('dim-label'); box.append(self.status)
        self.play = Gtk.Button(label='Play Roblox'); self.play.add_css_class('suggested-action')
        self.play.connect('clicked', self.on_play); box.append(self.play)
        self.set_values(load_settings())

    def set_values(self, settings):
        for key, dropdown in self.controls.items():
            values = [v for _, v in OPTIONS[key]]
            dropdown.set_selected(values.index(settings[key]))
        self.multi.set_active(settings['multithreaded'])

    def apply_preset(self, _button, name):
        self.set_values(PRESETS[name])
        self.status.set_text(f'{name} preset selected. Press Play to save it.')

    def on_play(self, _button):
        settings = {key: OPTIONS[key][dropdown.get_selected()][1] for key, dropdown in self.controls.items()}
        settings['multithreaded'] = self.multi.get_active()
        try:
            save_settings(settings)
        except OSError as error:
            self.status.set_text(f'Could not save settings: {error}')
            return
        self.play.set_sensitive(False)
        self.status.set_text('Checking for Mocktail updates, then starting Roblox…')
        threading.Thread(target=self.launch, args=(settings,), daemon=True).start()

    def launch(self, settings):
        try:
            seily.prepare_runtime()
            env = seily.runtime_environment(settings)
            log = seily.ROOT / 'launcher.log'
            with log.open('a') as output:
                subprocess.Popen([str(seily.RUNTIME)], env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            GLib.idle_add(self.close)
        except (OSError, RuntimeError) as error:
            GLib.idle_add(self.failed, str(error))

    def failed(self, message):
        self.status.set_text(f'Could not start Seily: {message}')
        self.play.set_sensitive(True)


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='io.github.seily.Launcher', flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self):
        window = self.props.active_window or Window(self)
        window.present()


if __name__ == '__main__':
    App().run(None)
