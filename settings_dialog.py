#!/usr/bin/env python3
"""The settings of the py-words runner, in a small window:

    python3 settings_dialog.py [--py-words FOLDER]

The prefix of a search (la amicorum), the language of the meanings and
that of the interface (those of py-words, or others for KRunner only), and
how many results to show.  They are saved in runner_settings.path(); the
runner sees them at the next query.  The window has the look of py-words
(its dark mode, its fonts) and speaks the language of the interface
chosen (English or Spanish).
"""

import argparse
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import dictionary
import runner_settings
from runner_settings import MOST_RESULTS, RunnerSettings, good_prefix

#  The languages of the interface (those of TEXTS)
INTERFACES = {'en': 'English', 'es': 'Spanish'}

TEXTS = {
    'Settings of py-words in KRunner': 'Ajustes de py-words en KRunner',
    'Language of the meanings': 'Idioma de los significados',
    'Language of the interface': 'Idioma de la interfaz',
    'Prefix': 'Prefijo',
    'English': 'Inglés',
    'Spanish': 'Español',
    'The prefix is a word, without spaces.':
        'El prefijo es una palabra, sin espacios.',
    'As in py-words ({language})': 'Como en py-words ({language})',
    'Results, at most': 'Resultados, como máximo',
    'In KRunner, type: {prefix} WORD, or {prefix} ~e WORD to Latin.\n'
    'Changes are seen at the next search.':
        'En KRunner, escriba: {prefix} PALABRA, o {prefix} ~e PALABRA hacia '
        'el latín.\nLos cambios se ven en la búsqueda siguiente.',
    'Save': 'Guardar',
    'Cancel': 'Cancelar',
    'Cannot save the settings: {error}':
        'No se pueden guardar los ajustes: {error}',
}


class Dialog:

    def __init__(self, root: tk.Tk):
        import config
        import interface
        import languages
        from lexicon import default_datadir
        from settings import Settings
        self.root = root
        datadir = default_datadir()
        usual = Settings()
        usual.load(datadir)
        saved = runner_settings.load()
        interface.use(saved.interface or usual.interface)
        self.spanish = interface.code() == 'es'
        self.tr = interface.tr
        names = languages.names(datadir)
        self.codes = [''] + list(names)
        choices = [self.t('As in py-words ({language})').format(
            language=self.tr(names.get(usual.language, usual.language)))]
        choices += [self.tr(names[code]) for code in names]
        self.interfaces = [''] + list(INTERFACES)
        py_words_ui = usual.interface if usual.interface in INTERFACES \
            else 'en'
        interfaces = [self.t('As in py-words ({language})').format(
            language=self.t(INTERFACES[py_words_ui]))]
        interfaces += [self.t(INTERFACES[code]) for code in INTERFACES]
        self._look()

        root.title(self.t('Settings of py-words in KRunner'))
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        def label(row, text):
            ttk.Label(frame, text=self.t(text)).grid(
                row=row, column=0, sticky='w', padx=(0, 12), pady=4)
        label(0, 'Prefix')
        self.prefix = tk.StringVar(value=saved.prefix)
        ttk.Entry(frame, textvariable=self.prefix, width=8).grid(
            row=0, column=1, sticky='w', pady=4)
        label(1, 'Language of the meanings')
        self.language = ttk.Combobox(frame, values=choices, state='readonly',
                                     width=28)
        self.language.current(self.codes.index(saved.language)
                              if saved.language in self.codes else 0)
        self.language.grid(row=1, column=1, sticky='we', pady=4)
        label(2, 'Language of the interface')
        self.interface = ttk.Combobox(frame, values=interfaces,
                                      state='readonly', width=28)
        self.interface.current(self.interfaces.index(saved.interface)
                               if saved.interface in self.interfaces else 0)
        self.interface.grid(row=2, column=1, sticky='we', pady=4)
        label(3, 'Results, at most')
        self.results = tk.IntVar(value=saved.results)
        ttk.Spinbox(frame, from_=1, to=MOST_RESULTS, width=5,
                    textvariable=self.results).grid(row=3, column=1,
                                                    sticky='w', pady=4)
        self.note = ttk.Label(frame, style='Muted.TLabel', justify='left')
        self.note.grid(row=4, column=0, columnspan=2, sticky='w',
                       pady=(12, 0))
        self.prefix.trace_add('write', lambda *_: self._show_note())
        self._show_note()
        buttons = ttk.Frame(frame, padding=(0, 16, 0, 0))
        buttons.grid(row=5, column=0, columnspan=2, sticky='we')
        save = ttk.Button(buttons, text=self.t('Save'), command=self.save)
        save.pack(side='right')
        ttk.Button(buttons, text=self.t('Cancel'),
                   command=root.destroy).pack(side='right', padx=(0, 6))
        root.bind('<Return>', lambda e: self.save())
        root.bind('<Escape>', lambda e: root.destroy())
        save.focus_set()
        root.resizable(False, False)
        self._to_front()

    def _to_front(self):
        """Brings the window to the front: started from the runner (in
        the background), KWin would put it behind the others."""
        root = self.root
        root.lift()
        root.attributes('-topmost', True)
        root.after(300, lambda: root.attributes('-topmost', False))
        root.after(50, root.focus_force)

    def _show_note(self):
        """How to search, with the prefix being typed."""
        prefix = good_prefix(self.prefix.get())
        if prefix is None:
            text = self.t('The prefix is a word, without spaces.')
        else:
            text = self.t(
                'In KRunner, type: {prefix} WORD, or {prefix} ~e WORD to '
                'Latin.\nChanges are seen at the next search.').format(
                    prefix=prefix)
        self.note.config(text=text)

    def t(self, english: str) -> str:
        return TEXTS.get(english, english) if self.spanish else english

    def _look(self):
        """The dark mode and fonts of py-words, if they can be had."""
        try:
            from gui_fonts import Fonts
            from gui_theme import Theme
            Fonts.of(self.root)
            Theme.of(self.root)
        except Exception:
            pass

    def chosen(self) -> RunnerSettings:
        try:
            results = int(self.results.get())
        except (tk.TclError, ValueError):
            results = runner_settings.RESULTS
        return RunnerSettings(
            language=self.codes[self.language.current()],
            results=min(max(results, 1), MOST_RESULTS),
            prefix=good_prefix(self.prefix.get()) or runner_settings.PREFIX,
            interface=self.interfaces[self.interface.current()])

    def save(self):
        if good_prefix(self.prefix.get()) is None:
            messagebox.showerror(parent=self.root, message=self.t(
                'The prefix is a word, without spaces.'))
            return
        try:
            runner_settings.save(self.chosen())
        except OSError as e:
            messagebox.showerror(
                parent=self.root, message=self.t(
                    'Cannot save the settings: {error}').format(
                        error=e.strerror))
            return
        self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='The settings of py-words in KRunner.')
    parser.add_argument('--py-words', default=dictionary.PY_WORDS,
                        metavar='FOLDER', help='the folder of py-words '
                        f'(default: {dictionary.PY_WORDS})')
    args = parser.parse_args(argv)
    try:
        dictionary.use(args.py_words)
    except FileNotFoundError as e:
        sys.exit(f'settings_dialog.py: {e}')
    root = tk.Tk(className='krunner-py-words')
    Dialog(root)
    root.mainloop()


if __name__ == '__main__':
    main()
