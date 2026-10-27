#!/usr/bin/env python3
"""Installs (or, with --uninstall, removes) the py-words runner for the
current user:

    ~/.local/share/krunner/dbusplugins/py-words.desktop     tells KRunner
    ~/.local/share/dbus-1/services/SERVICE.service          starts it
    ~/.local/share/applications/krunner-py-words-settings.desktop
                                            the settings, in the menu

    python3 install.py [--py-words FOLDER] [--uninstall]

(uninstall.py is the same as --uninstall.)

Then restart KRunner (kquitapp6 krunner; it starts again when called).
"""

import argparse
import os
import signal
import subprocess
import sys

from krunner_py_words import HERE, PATH, PREFIX, PY_WORDS, SERVICE

DATA = os.environ.get('XDG_DATA_HOME') or \
    os.path.expanduser('~/.local/share')
PLUGIN = os.path.join(DATA, 'krunner', 'dbusplugins', 'py-words.desktop')
STARTER = os.path.join(DATA, 'dbus-1', 'services', SERVICE + '.service')
MENU = os.path.join(DATA, 'applications', 'krunner-py-words-settings.desktop')

DESKTOP = f"""[Desktop Entry]
Name=py-words
Comment=Latin dictionary: {PREFIX} WORD, or {PREFIX} ~e WORD to Latin
Icon=accessories-dictionary
Type=Service
X-KDE-PluginInfo-Author=Nicolas Vaughan
X-KDE-PluginInfo-Name=py-words
X-KDE-PluginInfo-Version=0.1
X-KDE-PluginInfo-License=GPL-3.0-or-later
X-KDE-PluginInfo-EnabledByDefault=true
X-Plasma-API=DBus
X-Plasma-API-Minimum-Version=2.0
X-Plasma-DBusRunner-Service={SERVICE}
X-Plasma-DBusRunner-Path={PATH}
X-Plasma-Runner-Min-Letter-Count=3
"""


def menu(py_words: str) -> str:
    program = os.path.join(HERE, 'settings_dialog.py')
    return ('[Desktop Entry]\nType=Application\n'
            'Name=py-words in KRunner\n'
            'Name[es]=py-words en KRunner\n'
            'Comment=Settings of the py-words runner\n'
            'Comment[es]=Ajustes del lanzador de py-words\n'
            f'Exec={sys.executable} {program} --py-words {py_words}\n'
            'Icon=accessories-dictionary\n'
            'Categories=Settings;Utility;\n')


def stop_runner() -> None:
    """Stops the runner, if it is running: the Python processes whose
    program is krunner_py_words.py (not an editor or a shell that only
    names it)."""
    program = os.path.realpath(os.path.join(HERE, 'krunner_py_words.py'))
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                argv = f.read().split(b'\0')
        except OSError:
            continue
        if len(argv) > 1 and b'python' in os.path.basename(argv[0]) and \
                os.path.realpath(argv[1].decode(errors='replace')) == program:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass


def service(py_words: str) -> str:
    program = os.path.join(HERE, 'krunner_py_words.py')
    return (f'[D-BUS Service]\nName={SERVICE}\n'
            f'Exec={sys.executable} {program} --py-words {py_words}\n')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Install the py-words runner for KRunner.')
    parser.add_argument('--py-words', default=PY_WORDS, metavar='FOLDER',
                        help=f'the folder of py-words (default: {PY_WORDS})')
    parser.add_argument('--uninstall', action='store_true',
                        help='remove the runner')
    args = parser.parse_args(argv)
    if args.uninstall:
        for path in (PLUGIN, STARTER, MENU):
            if os.path.exists(path):
                os.remove(path)
                print(f'Removed {path}')
    else:
        py_words = os.path.abspath(os.path.expanduser(args.py_words))
        if not os.path.isfile(os.path.join(py_words, 'words.py')):
            sys.exit(f'install.py: py-words is not in {py_words} '
                     '(see --py-words)')
        for path, text in ((PLUGIN, DESKTOP), (STARTER, service(py_words)),
                           (MENU, menu(py_words))):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f'Wrote {path}')
    #  (D-Bus reads its .service files again: it does not watch a folder
    #  made after the session started)
    subprocess.run(['busctl', '--user', 'call', 'org.freedesktop.DBus',
                    '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                    'ReloadConfig'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #  (the application menu sees the settings entry at once)
    subprocess.run(['kbuildsycoca6'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #  (a runner that is running keeps its old files)
    stop_runner()
    subprocess.run(['kquitapp6', 'krunner'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('KRunner restarted.')


if __name__ == '__main__':
    main()
