krunner-py-words
================

[py-words](https://github.com/nivaca/py-words), the Latin dictionary, in
KRunner (KDE Plasma 6): type `pw` and a Latin word, and its entries
appear as you type.

    pw amicorum         Latin to the language of the meanings
    pw rem acu tetigisti    a whole line
    pw ~e friend        that language to Latin (also pw ~e love V)

Each match is an entry: its dictionary form as the title, and below it the
meaning and the forms (`amīc-ōrum GEN.PL`).  Enter opens the search in
the window of py-words; the actions copy the results of that entry, open
the search in the dictionary online, and open the settings of the runner.  The results follow the settings of
py-words (the glosses, the near spellings ...), as the window and the
command line do, and a change of settings is seen at the next query.

Settings
--------

In KRunner, `pw ?` (or `pw settings`, `pw ajustes`) gives a single match,
"py-words settings", that opens a small window with the settings of the
runner itself.  So do "py-words in KRunner" in the application menu, the
Settings action of each match, and `python3 settings_dialog.py`:

- the prefix that starts a search (`pw` as usual): a word, without
  spaces;
- the language of the meanings: as in py-words, or English or Spanish
  for KRunner only (`pw ~e WORD` then looks for a word of that language);
- the language of the interface (of this window and of the actions in
  KRunner): as in py-words, or English or Spanish;
- how many results to show, at most (12 as usual).

They are kept in `~/.config/krunner-py-words/settings.ini`, and seen at
the next search.

Installing
----------

It needs py-words (by default in the folder `py-words` next to this one),
and the D-Bus bindings of Python, which Fedora KDE usually has already:

    $ sudo dnf install python3-dbus python3-gobject

Then:

    $ python3 install.py [--py-words FOLDER]

This writes three files, and restarts KRunner:

- `~/.local/share/krunner/dbusplugins/py-words.desktop`: tells KRunner
  about the runner.  KRunner sends it every query; the runner answers only
  those that start with the prefix.
- `~/.local/share/dbus-1/services/io.github.nivaca.PyWordsKRunner.service`:
  lets D-Bus start `krunner_py_words.py` the first time KRunner needs
  it.  It stays running, with the dictionary loaded, so each query is
  quick.
- `~/.local/share/applications/krunner-py-words-settings.desktop`: the
  settings, in the application menu.

`python3 uninstall.py` (or `python3 install.py --uninstall`) removes
them, stops the runner and restarts KRunner; this folder and py-words are
left as they are.  After changing the program
or moving py-words, run `install.py` again (it also stops the running
runner).  The runner can be turned off in System Settings > Search >
KRunner.

How it works
------------

- `krunner_py_words.py`: the D-Bus runner (the interface
  `org.kde.krunner1`: Actions, Match, Run).
- `dictionary.py`: the matches for a query, from py-words; it knows
  nothing of D-Bus.
- `settings_dialog.py`: the settings window; `runner_settings.py`: the
  file that keeps them.
- `install.py`: the three files above; `uninstall.py` removes them.
- `tests/`: `python3 -m unittest discover -s tests`.

To see what it does, stop it (`python3 -c 'import install;
install.stop_runner()'`) and start it by hand, `python3
krunner_py_words.py`: its errors are written to the terminal.

Licence
-------

GNU General Public License, version 3 or later (see LICENCE.txt), as
py-words.  © 2026 Nicolas Vaughan.
