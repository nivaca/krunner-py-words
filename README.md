krunner-py-words
================

[py-words](https://github.com/nivaca/py-words), the Latin dictionary, in
KRunner (KDE Plasma 6): type `la` and a Latin word, and its entries
appear as you type.

    la amicorum         Latin to the language of the meanings
    la rem acu tetigisti    a whole line
    la ~e friend        that language to Latin (also la ~e love V)

Each match is an entry: its dictionary form as the title, and below it the
meaning and the forms (`amīc-ōrum GEN.PL`).  Enter copies the results of
that entry; the second action opens the search in the dictionary online.
The results follow the settings of py-words (the language of the
meanings, the glosses, the near spellings ...), as the window and the
command line do, and a change of settings is seen at the next query.

Installing
----------

It needs py-words (by default in the folder `py-words` next to this one),
and the D-Bus bindings of Python, which Fedora KDE usually has already:

    $ sudo dnf install python3-dbus python3-gobject

Then:

    $ python3 install.py [--py-words FOLDER]

This writes two files, and restarts KRunner:

- `~/.local/share/krunner/dbusplugins/py-words.desktop`: tells KRunner
  about the runner, and that only queries starting with `la ` are for it.
- `~/.local/share/dbus-1/services/io.github.nivaca.PyWordsKRunner.service`:
  lets D-Bus start `krunner_py_words.py` the first time KRunner needs
  it.  It stays running, with the dictionary loaded, so each query is
  quick.

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
- `install.py`: the two files above; `uninstall.py` removes them.
- `tests/`: `python3 -m unittest discover -s tests`.

To see what it does, stop it (`pkill -f krunner_py_words.py`) and start it
by hand, `python3 krunner_py_words.py`: its errors are written to the
terminal.

Licence
-------

GNU General Public License, version 3 or later (see LICENCE.txt), as
py-words.  © 2026 Nicolas Vaughan.
