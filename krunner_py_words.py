#!/usr/bin/env python3
"""py-words in KRunner: type "la amicorum" (or "la ~e friend") and the
results appear as you type.

A D-Bus runner (the interface org.kde.krunner1): KRunner calls Match for
each query that starts with the prefix (see the .desktop file that
install.py writes), and Run when a match is chosen.  D-Bus starts this
program the first time it is needed; it stays, with the dictionary loaded.

    python3 krunner_py_words.py [--py-words FOLDER]

Enter copies the results of the match; the second action opens the search
in the dictionary online.  Needs python3-dbus and python3-gobject.
"""

import argparse
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

SERVICE = 'io.github.nivaca.PyWordsKRunner'
PATH = '/runner'
IFACE = 'org.kde.krunner1'
#  What starts a query: "la amicorum"
PREFIX = 'la '
ICON = 'accessories-dictionary'
#  KRunner's types of match (KRunner::QueryMatch::CategoryRelevance)
EXACT = 100

HERE = os.path.dirname(os.path.abspath(__file__))
#  py-words, if --py-words does not say: next to this folder
PY_WORDS = os.path.join(os.path.dirname(HERE), 'py-words')


def strip_prefix(query: str) -> str | None:
    """The query without PREFIX, or None if it is not for us."""
    if query.lower().startswith(PREFIX):
        return query[len(PREFIX):]
    return None


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

    def __init__(self, bus, words: dictionary.Dictionary):
        super().__init__(bus, PATH)
        self.words = words
        self.found: dict[str, dictionary.Match] = {}   # (of the last query)

    @dbus.service.method(IFACE, out_signature='a(sss)')
    def Actions(self):
        return [('online', 'Open online', 'internet-web-browser')]

    @dbus.service.method(IFACE, in_signature='s',
                         out_signature='a(sssida{sv})')
    def Match(self, query):
        text = strip_prefix(str(query))
        if text is None or not text.strip():
            return []
        try:
            matches = self.words.matches(text)
        except Exception as e:          # (KRunner shows nothing, else)
            print(f'krunner-py-words: {text!r}: {e!r}', file=sys.stderr)
            return []
        self.found = {}
        out = []
        for i, m in enumerate(matches):
            key = str(i)
            self.found[key] = m
            properties = dbus.Dictionary(
                {'subtext': m.subtext, 'multiline': True,
                 'category': 'py-words'}, signature='sv')
            out.append((key, m.text, ICON, EXACT, 1.0 - i / 100,
                        properties))
        return out

    @dbus.service.method(IFACE, in_signature='ss')
    def Run(self, key, action):
        m = self.found.get(str(key))
        if m is None:
            return
        if action == 'online':
            webbrowser.open(m.url)
        else:
            copy_text(m.full)


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
    runner = Runner(bus, words)         # noqa: F841
    GLib.MainLoop().run()


if __name__ == '__main__':
    main()
