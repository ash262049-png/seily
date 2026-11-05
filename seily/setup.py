#!/usr/bin/env python3
"""Seily's local setup and launch window."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib, Gtk, GdkPixbuf

import seily

SETTINGS = seily.ROOT / 'settings.json'
PRESETS = {
    'Balanced': {'fps': 'display', 'vsync': 'auto', 'backend': 'direct-vulkan', 'multithreaded': False, 'texture': 'default'},
    'Maximum FPS': {'fps': 'unlimited', 'vsync': 'off', 'backend': 'direct-vulkan', 'multithreaded': True, 'texture': '2'},
    'Roblox defaults': {'fps': '-1', 'vsync': 'auto', 'backend': 'direct-vulkan', 'multithreaded': False, 'texture': 'default'},
}
OPTIONS = {
    'fps': [('Roblox default', '-1'), ('Display refresh rate', 'display'), ('Uncapped (request 9999 FPS)', 'unlimited'), ('60 FPS', '60'), ('120 FPS', '120'), ('144 FPS', '144'), ('240 FPS', '240')],
    'vsync': [('Automatic', 'auto'), ('Off (may tear)', 'off'), ('On', 'on')],
    'backend': [('Vulkan (recommended)', 'direct-vulkan'), ('OpenGL', 'opengl'), ('System default', 'system'), ('ANGLE over Vulkan', 'angle-vulkan')],
    'texture': [('Automatic (Roblox / Mocktail)', 'default'), ('Balanced (mip bias 1)', '1'), ('Lower detail (mip bias 2)', '2')],
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
        self.set_default_size(640, 760)
        self.set_icon_name('seily')
        scroll = Gtk.ScrolledWindow()
        self.set_child(scroll)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_size_request(560, -1)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.START)
        box.set_margin_top(48); box.set_margin_bottom(48)
        box.set_margin_start(24); box.set_margin_end(24)
        scroll.set_child(box)
        header = Gtk.Box(spacing=16)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(Path(__file__).with_name('seily.png')), 48, 48, True)
        logo = Gtk.Image.new_from_pixbuf(pixbuf)
        header.append(logo)
        headings = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        title = Gtk.Label(label='Seily'); title.add_css_class('title-1'); title.set_xalign(0)
        desc = Gtk.Label(label='Roblox for Linux'); desc.set_xalign(0); desc.add_css_class('dim-label')
        headings.append(title); headings.append(desc); header.append(headings)
        box.append(header)

        intro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        intro.set_margin_top(12)
        label = Gtk.Label(label='Ready to play?'); label.set_xalign(0); label.add_css_class('section-title'); intro.append(label)
        subtitle = Gtk.Label(label='Pick a preset or fine-tune your settings below.')
        subtitle.set_xalign(0); subtitle.add_css_class('dim-label'); intro.append(subtitle)
        box.append(intro)

        buttons = Gtk.Box(spacing=8)
        for name in PRESETS:
            button = Gtk.Button(label=name)
            button.connect('clicked', self.apply_preset, name)
            button.set_hexpand(True); buttons.append(button)
        box.append(buttons)

        settings_label = Gtk.Label(label='GRAPHICS & PERFORMANCE'); settings_label.set_xalign(0)
        settings_label.add_css_class('eyebrow'); settings_label.set_margin_top(8); box.append(settings_label)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.add_css_class('settings-card')
        self.controls = {}
        for key, label in [('fps', 'Frame rate'), ('vsync', 'Vertical sync'), ('backend', 'Renderer'), ('texture', 'Texture detail')]:
            row = Gtk.Box(spacing=16); row.add_css_class('setting-row')
            heading = Gtk.Label(label=label); heading.set_xalign(0); heading.set_hexpand(True)
            row.append(heading)
            dropdown = Gtk.DropDown.new_from_strings([name for name, _ in OPTIONS[key]])
            dropdown.set_size_request(255, -1)
            row.append(dropdown); self.controls[key] = dropdown; card.append(row)
            card.append(Gtk.Separator())
        row = Gtk.Box(spacing=16); row.add_css_class('setting-row')
        label = Gtk.Label(label='Multithreaded rendering'); label.set_xalign(0); label.set_hexpand(True)
        self.multi = Gtk.Switch(); self.multi.set_valign(Gtk.Align.CENTER)
        row.append(label); row.append(self.multi); card.append(row); box.append(card)

        note = Gtk.Label(label='Texture detail is experimental and may be ignored by Roblox. You can also lower graphics quality in game.')
        note.set_wrap(True); note.set_xalign(0); note.add_css_class('dim-label'); box.append(note)
        self.status = Gtk.Label(label='Save your settings or start Roblox.')
        self.status.set_wrap(True); self.status.set_xalign(0); self.status.add_css_class('dim-label'); box.append(self.status)
        actions = Gtk.Box(spacing=8)
        save = Gtk.Button(label='Save settings'); save.connect('clicked', self.on_save)
        actions.append(save)
        self.play = Gtk.Button(label='Play Roblox  →'); self.play.add_css_class('suggested-action')
        self.play.set_hexpand(True); self.play.connect('clicked', self.on_play); actions.append(self.play)
        box.append(actions)
        self.set_values(load_settings())

    def set_values(self, settings):
        for key, dropdown in self.controls.items():
            values = [v for _, v in OPTIONS[key]]
            dropdown.set_selected(values.index(settings[key]))
        self.multi.set_active(settings['multithreaded'])

    def apply_preset(self, _button, name):
        self.set_values(PRESETS[name])
        self.status.set_text(f'{name} preset selected. Save your settings or press Play.')

    def current_settings(self):
        settings = {key: OPTIONS[key][dropdown.get_selected()][1] for key, dropdown in self.controls.items()}
        settings['multithreaded'] = self.multi.get_active()
        return settings

    def on_save(self, _button):
        try:
            save_settings(self.current_settings())
        except OSError as error:
            self.status.set_text(f'Could not save settings: {error}')
            return False
        self.status.set_text('Settings saved. Seily will use them next time you play.')
        return True

    def on_play(self, _button):
        if not self.on_save(None):
            return
        settings = self.current_settings()
        self.play.set_sensitive(False)
        self.status.set_text('Checking for Mocktail updates, then starting Roblox…')
        threading.Thread(target=self.launch, args=(settings,), daemon=True).start()

    def launch(self, settings):
        try:
            seily.prepare_runtime()
            env = seily.runtime_environment(settings)
            command = seily.runtime_command()
            log = seily.ROOT / 'launcher.log'
            with log.open('a') as output:
                subprocess.Popen([str(command)], env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            GLib.idle_add(self.close)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            GLib.idle_add(self.failed, str(error))

    def failed(self, message):
        self.status.set_text(f'Could not start Seily: {message}')
        self.play.set_sensitive(True)


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='io.github.seily.Launcher', flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self):
        from gi.repository import Gdk
        css = Gtk.CssProvider()
        css.load_from_data(b'''
            window { background: #11151c; color: #eef1f5; }
            label.title-1 { font-size: 25px; font-weight: 750; color: #f7f9fc; }
            .section-title { font-size: 20px; font-weight: 700; }
            .eyebrow { color: #8a9bb0; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            .dim-label { color: #a4afbd; }
            .settings-card { background: #1a202a; border: 1px solid #303a47; border-radius: 12px; }
            .setting-row { padding: 10px 14px; }
            separator { background: #303a47; min-height: 1px; }
            button { border-radius: 8px; padding: 8px 12px; }
            button.suggested-action { background: #258ce0; color: white; font-weight: 700; padding: 13px; }
            dropdown > button { background: #252e3a; border: 1px solid #3b4756; color: #f0f4f8; }
            switch { border-radius: 14px; }
        ''')
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        window = self.props.active_window or Window(self)
        window.present()


if __name__ == '__main__':
    if sys.argv[1:] == ['--play']:
        try:
            seily.prepare_runtime()
            env = seily.runtime_environment(load_settings())
            command = seily.runtime_command()
            with (seily.ROOT / 'launcher.log').open('a') as log:
                os.dup2(log.fileno(), 1)
                os.dup2(log.fileno(), 2)
            os.execve(str(command), [str(command)], env)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            app = Gtk.Application(application_id='io.github.seily.LaunchError')
            def show_error(application):
                window = Gtk.ApplicationWindow(application=application, title='Seily could not start')
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
                for setter in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
                    setter(24)
                message = Gtk.Label(label=str(error)); message.set_wrap(True); box.append(message)
                close = Gtk.Button(label='Close'); close.connect('clicked', lambda _: window.close()); box.append(close)
                window.set_child(box); window.present()
            app.connect('activate', show_error)
            app.run(None)
            sys.exit(1)
    else:
        App().run(None)
