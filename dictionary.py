"""py-words for KRunner: the results of a query as short matches.

This part knows nothing of D-Bus, so it can be tested on its own.  It uses
the program in the folder of py-words (see `use`), with its settings: those
of the configuration file that the windows and the command line share.

    amicorum        Latin to the language of the meanings
    ~e friend       that language to Latin (and a part of speech: ~e love V)
"""

from __future__ import annotations

import copy
import os
import sys
import urllib.parse
from dataclasses import dataclass

import runner_settings

#  py-words, if no other folder is given: next to this one
PY_WORDS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'py-words')
#  The dictionary online, for the action "Open online"
ONLINE = 'https://nicolasvaughan.org/py-words/'


@dataclass
class Match:
    """One result for KRunner: TEXT (the dictionary form), SUBTEXT (the
    meaning, and the forms), FULL (what is copied) and URL (the search
    online)."""
    text: str
    subtext: str
    full: str
    url: str


def use(folder: str) -> None:
    """Makes the modules of py-words in FOLDER importable."""
    folder = os.path.abspath(os.path.expanduser(folder))
    if not os.path.isfile(os.path.join(folder, 'words.py')):
        raise FileNotFoundError(f'py-words is not in {folder}')
    if folder not in sys.path:
        sys.path.insert(0, folder)


class Dictionary:
    """py-words, loaded once.  `use` must be called first."""

    def __init__(self):
        import config
        import interface
        from lexicon import Lexicon, default_datadir
        self._config = config
        self._interface = interface
        self.datadir = default_datadir()
        self.lexicon = Lexicon.load(self.datadir)
        self._stamp = None
        self.session = None
        self.mine = runner_settings.RunnerSettings()
        self.most = runner_settings.RESULTS
        self.refresh()

    def languages(self) -> dict[str, str]:
        """{code: name} of the languages of the meanings."""
        import languages
        return languages.names(self.datadir)

    def refresh(self):
        """Reads the settings again if the configuration file of py-words
        (changed in the window, say) or that of the runner changed."""
        from session import Session
        from settings import Settings
        try:
            stamp = os.path.getmtime(self._config.config_path())
        except OSError:
            stamp = None
        stamp = (stamp, runner_settings.stamp())
        if self.session is not None and stamp == self._stamp:
            return
        self._stamp = stamp
        settings = Settings()
        settings.load(self.datadir)
        mine = runner_settings.load()
        if mine.language in self.languages():
            settings.language = mine.language
        self.mine = mine
        self.most = mine.results
        self._interface.use(mine.interface or settings.interface)
        self.session = Session(self.lexicon, settings)

    def _renderer(self):
        """The renderer of the session, without codes or entry numbers
        (there is no room for them)."""
        from render import Renderer
        s = copy.copy(self.session.settings)
        s.show_codes = s.show_entry_source = s.pearse_codes = False
        session = self.session
        return Renderer(s, False, self.lexicon.glosses, session.language,
                        self.lexicon.long_stems)

    def matches(self, query: str) -> list[Match]:
        """The matches for QUERY: Latin, or after ~e a word in the language
        of the meanings."""
        self.refresh()
        query = query.strip()
        if query[:2].lower() == '~e':
            return self._reverse(query[2:].strip())[:self.most]
        return self._latin(query)[:self.most]

    def _latin(self, line: str) -> list[Match]:
        az = self.session.analyzer
        out = []
        for result in az.analyze_line(line):
            if not result.unknown:
                out += self._readings(result)
                continue
            spellings = []
            s = self.session.settings
            if s.fuzzy_search:
                spellings = az.near_spellings(result.word)
            r = self._renderer()
            note = r.t('(unknown)')
            if spellings:
                note += '  ' + r.t(f'(near spellings: {", ".join(spellings)})')
            out.append(Match(result.word, note, f'{result.word}\n  {note}',
                             self._url(result.word)))
            for spelling in spellings:
                out += self._readings(az.analyze_word(spelling)[0])
        return out

    def _readings(self, result) -> list[Match]:
        """A match for each reading of RESULT (an entry, an irregular
        form, an affix ...), as the command line writes them."""
        out = []
        shown = set()
        for reading in result.readings:
            r = self._renderer()
            r.reading(reading, result, shown)
            lines = [line.strip() for line in r.text().split('\n')
                     if line.strip()]
            if not lines:
                continue
            title, rest = lines[0], lines[1:]
            meaning = rest[0] if rest else ''
            forms = [' '.join(line.split()) for line in rest[1:]]
            subtext = meaning + ('\n' + '; '.join(forms) if forms else '')
            full = '\n'.join([result.word, '  ' + title] +
                             ['    ' + line for line in rest])
            out.append(Match(title, subtext, full, self._url(result.word)))
        return out

    def _reverse(self, line: str) -> list[Match]:
        from model import Pos
        words = line.split()
        if not words:
            return []
        pos = Pos.X
        if len(words) > 1 and words[1].upper() in Pos.__members__:
            pos = Pos[words[1].upper()]
        language = self.session.language
        hits = self.lexicon.reverse(language.code).search(words[0], pos)
        r = self._renderer()
        out = []
        for hit in hits[:self.most]:
            title = r.entry_header(hit.entry)
            meaning = r.meaning(hit.entry).lstrip('|').strip()
            out.append(Match(title, meaning,
                             f'{words[0]}\n  {title}\n    {meaning}',
                             self._url(words[0], language.code)))
        if not out:
            note = r.t('(no match)')
            out.append(Match(words[0], note, f'{words[0]}\n  {note}',
                             self._url(words[0], language.code)))
        return out

    @staticmethod
    def _url(word: str, lang: str = '') -> str:
        """The search for WORD online (in LANG: to Latin)."""
        params = {'q': word}
        if lang:
            params['lang'] = lang
        return ONLINE + '?' + urllib.parse.urlencode(params)
