"""Tests of the runner: the matches (with py-words next to this folder),
and the D-Bus methods called directly."""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import dictionary  # noqa: E402

PY_WORDS = os.path.join(os.path.dirname(HERE), 'py-words')


@unittest.skipUnless(os.path.isdir(PY_WORDS), 'needs py-words next to it')
class MatchTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        dictionary.use(PY_WORDS)
        cls.words = dictionary.Dictionary()

    def test_latin(self):
        found = self.words.matches('amicorum')
        self.assertTrue(found[0].text.startswith('amicus, amici'))
        self.assertIn('amīc-ōrum', found[0].subtext)
        self.assertTrue(found[0].full.startswith('amicorum\n  amicus'))
        self.assertTrue(found[0].url.endswith('?q=amicorum'))

    def test_unknown(self):
        found = self.words.matches('xqzv')
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].text, 'xqzv')

    def test_near_spelling(self):
        found = self.words.matches('amicuss')
        if self.words.session.settings.fuzzy_search:
            self.assertTrue(any(m.text.startswith('amicus, amici')
                                for m in found))

    def test_to_latin(self):
        code = self.words.session.language.code
        word = {'es': 'amigo'}.get(code, 'friend')
        found = self.words.matches(f'~e {word}')
        self.assertTrue(any(m.text.startswith('amicus') for m in found))
        self.assertIn(f'lang={code}', found[0].url)

    def test_at_most(self):
        self.assertLessEqual(len(self.words.matches('~e amigo')),
                             dictionary.MOST)
        self.assertEqual(self.words.matches('~e'), [])


class PrefixTests(unittest.TestCase):

    def test_prefix(self):
        try:
            import krunner_py_words as k
        except ImportError:
            self.skipTest('needs python3-dbus and python3-gobject')
        self.assertEqual(k.strip_prefix('la amicorum'), 'amicorum')
        self.assertEqual(k.strip_prefix('La amicorum'), 'amicorum')
        self.assertIsNone(k.strip_prefix('firefox'))
        self.assertIsNone(k.strip_prefix('lamp'))


if __name__ == '__main__':
    unittest.main()
