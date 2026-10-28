#!/usr/bin/env python3
"""py-words in KRunner: type "pw amicorum" (or "pw ~e friend") and the
results appear as you type.

A D-Bus runner (the interface org.kde.krunner1): KRunner calls Match for
each query that starts with the prefix (see the .desktop file that
install.py writes), and Run when a match is chosen.  D-Bus starts this
program the first time it is needed; it stays, with the dictionary loaded.

    python3 krunner_py_words.py [--py-words FOLDER]

Enter opens the search in the window of py-words (words_gui.py); the
actions copy the results of the match, open the search in the dictionary
online, and open the settings of the runner (settings_dialog.py).  "pw ?" (or "pw settings", "pw ajustes") gives a
single match that opens the settings.  Needs python3-dbus and python3-gobject.
"""

import argparse
import html
import os
import shutil
import subprocess
import sys
import webbrowser

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

import dictionary
import runner_settings

SERVICE = 'io.github.nivaca.PyWordsKRunner'
PATH = '/runner'
IFACE = 'org.kde.krunner1'
#  What starts a query, as usual (the settings can change it): pw amicorum
PREFIX = runner_settings.PREFIX
ICON = 'accessories-dictionary'
#  KRunner's types of match (KRunner::QueryMatch::CategoryRelevance)
EXACT = 100

HERE = os.path.dirname(os.path.abspath(__file__))
PY_WORDS = dictionary.PY_WORDS


def strip_prefix(query: str, prefix: str = PREFIX) -> str | None:
    """The query without PREFIX and a space, or None if it is not for
    us."""
    start = prefix.lower() + ' '
    if query.lower().startswith(start):
        return query[len(start):]
    return None


#  The names of the actions, in the language of the interface
ACTIONS = {'en': ('Copy', 'Open online', 'Settings'),
           'es': ('Copiar', 'Abrir en línea', 'Ajustes')}
#  What asks for the settings, after the prefix: pw ?
ASK_SETTINGS = ('?', 'settings', 'ajustes')
#  The match that opens them: its title and subtext
SETTINGS_MATCH = {
    'en': ('py-words settings',
           'The prefix, the languages and the number of results'),
    'es': ('Ajustes de py-words',
           'El prefijo, los idiomas y el número de resultados')}


def asks_settings(text: str) -> bool:
    """Whether TEXT (the query without the prefix) asks for the
    settings."""
    return text.strip().lower() in ASK_SETTINGS


def display(m: dictionary.Match) -> str:
    """What KRunner shows of M: the dictionary form in bold, then the
    meaning and the forms.  (KRunner shows the subtext only for the
    selected match, on one line beside the text: the long dictionary forms
    leave it no room.  A multiline text is styled text, so it is escaped.)"""
    lines = [f'<b>{html.escape(m.text)}</b>']
    meaning, _, forms = m.subtext.partition('\n')
    if meaning:
        lines.append(html.escape(meaning))
    if forms:
        lines.append(f'<i>{html.escape(forms)}</i>')
    return '<br>'.join(lines)


def copy_text(text: str) -> None:
    """Puts TEXT in the clipboard: through Klipper, or else wl-copy or
    xclip."""
    try:
        klipper = dbus.SessionBus().get_object('org.kde.klipper', '/klipper')
        klipper.setClipboardContents(text,
                                     dbus_interface='org.kde.klipper.klipper')
        return
    except dbus.DBusException:
        pass
    for command in (['wl-copy'], ['xclip', '-selection', 'clipboard']):
        if shutil.which(command[0]):
            subprocess.run(command, input=text.encode(), check=False)
            return


class Runner(dbus.service.Object):

    def __init__(self, bus, words: dictionary.Dictionary, py_words: str):
        super().__init__(bus, PATH)
        self.words = words
        self.py_words = py_words
        self.found: dict[str, dictionary.Match] = {}   # (of the last query)
        self.query = ''                                 # (the last query)

    @dbus.service.method(IFACE, out_signature='a(sss)')
    def Actions(self):
        import interface
        self.words.refresh()
        copy, online, settings = ACTIONS.get(interface.code(), ACTIONS['en'])
        return [('copy', copy, 'edit-copy'),
                ('online', online, 'internet-web-browser'),
                ('settings', settings, 'configure')]

    @dbus.service.method(IFACE, in_signature='s',
                         out_signature='a(sssida{sv})')
    def Match(self, query):
        self.words.refresh()
        text = strip_prefix(str(query), self.words.mine.prefix)
        if text is None or not text.strip():
            return []
        if asks_settings(text):
            import interface
            title, subtext = SETTINGS_MATCH.get(interface.code(),
                                                SETTINGS_MATCH['en'])
            self.found = {}
            return [('settings', title, 'configure', EXACT, 1.0,
                     dbus.Dictionary(
                         {'subtext': subtext, 'category': 'py-words',
                          'actions': dbus.Array([], signature='s')},
                         signature='sv'))]
        try:
            matches = self.words.matches(text)
        except Exception as e:          # (KRunner shows nothing, else)
            print(f'krunner-py-words: {text!r}: {e!r}', file=sys.stderr)
            return []
        self.found = {}
        self.query = text
        out = []
        for i, m in enumerate(matches):
            key = str(i)
            self.found[key] = m
            properties = dbus.Dictionary(
                {'multiline': True, 'category': 'py-words'}, signature='sv')
            out.append((key, display(m), ICON, EXACT, 1.0 - i / 100,
                        properties))
        return out

    @dbus.service.method(IFACE, in_signature='ss')
    def Run(self, key, action):
        if str(key) == 'settings' or action == 'settings':
            self.open_settings()
            return
        m = self.found.get(str(key))
        if m is None:
            return
        if action == 'online':
            webbrowser.open(m.url)
        elif action == 'copy':
            copy_text(m.full)
        else:
            self.open_window(self.query)

    def open_window(self, query: str):
        """The window of py-words, looking QUERY up (after ~e: to
        Latin)."""
        query = query.strip()
        args = []
        if query[:2].lower() == '~e':
            args, query = ['-e'], query[2:].strip()
        subprocess.Popen([sys.executable,
                          os.path.join(self.py_words, 'words_gui.py')] +
                         args + query.split(),
                         cwd=self.py_words)

    def open_settings(self):
        subprocess.Popen([sys.executable,
                          os.path.join(HERE, 'settings_dialog.py'),
                          '--py-words', self.py_words])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='py-words in KRunner (a D-Bus runner).')
    parser.add_argument('--py-words', default=PY_WORDS, metavar='FOLDER',
                        help=f'the folder of py-words (default: {PY_WORDS})')
    args = parser.parse_args(argv)
    dictionary.use(args.py_words)
    words = dictionary.Dictionary()     # (before taking the name: loaded)
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName(SERVICE, bus)  # noqa: F841 (kept)
    runner = Runner(bus, words, args.py_words)  # noqa: F841
    GLib.MainLoop().run()


if __name__ == '__main__':
    main()
