"""The settings of the runner itself (those of the results come from
py-words): ~/.config/krunner-py-words/settings.ini

    [runner]
    prefix = pw         ; what starts a search in KRunner: pw amicorum
    language = es       ; the meanings (empty: as py-words says)
    interface = es      ; the settings and the actions (empty: as py-words)
    results = 12        ; at most so many matches

(Not settings.py: py-words has a module of that name.)
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass

SECTION = 'runner'
PREFIX = 'pw'                   # (as usual)
RESULTS = 12                    # (as usual)
MOST_RESULTS = 50


def path() -> str:
    base = os.environ.get('XDG_CONFIG_HOME') or \
        os.path.expanduser('~/.config')
    return os.path.join(base, 'krunner-py-words', 'settings.ini')


@dataclass
class RunnerSettings:
    language: str = ''          # ('': that of py-words)
    results: int = RESULTS
    prefix: str = PREFIX
    interface: str = ''         # ('': that of py-words)


def good_prefix(text: str) -> str | None:
    """TEXT as a prefix (a word, without spaces), or None if it cannot
    be one."""
    text = text.strip()
    if not text or any(c.isspace() for c in text):
        return None
    return text


def load() -> RunnerSettings:
    """The saved settings (the usual ones where the file has nothing, or
    something wrong)."""
    parser = configparser.ConfigParser()
    try:
        parser.read(path(), encoding='utf-8')
    except configparser.Error:
        return RunnerSettings()
    section = parser[SECTION] if parser.has_section(SECTION) else {}
    s = RunnerSettings(language=section.get('language', '').strip(),
                       interface=section.get('interface', '').strip(),
                       prefix=good_prefix(section.get('prefix', PREFIX)) or
                       PREFIX)
    try:
        s.results = min(max(int(section.get('results', RESULTS)), 1),
                        MOST_RESULTS)
    except ValueError:
        pass
    return s


def save(s: RunnerSettings) -> None:
    parser = configparser.ConfigParser()
    parser[SECTION] = {'prefix': s.prefix, 'language': s.language,
                       'interface': s.interface, 'results': str(s.results)}
    os.makedirs(os.path.dirname(path()), exist_ok=True)
    tmp = path() + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        parser.write(f)
    os.replace(tmp, path())


def stamp() -> float | None:
    """When the file was last saved (None: there is none)."""
    try:
        return os.path.getmtime(path())
    except OSError:
        return None
