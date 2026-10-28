"""Tests of the settings of the runner (runner_settings.py), and that the
matches follow them."""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import dictionary  # noqa: E402
import runner_settings  # noqa: E402
from runner_settings import RunnerSettings  # noqa: E402

PY_WORDS = os.path.join(os.path.dirname(HERE), 'py-words')


class SettingsTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get('XDG_CONFIG_HOME')
        os.environ['XDG_CONFIG_HOME'] = self.tmp.name

    def tearDown(self):
        if self.old is None:
            del os.environ['XDG_CONFIG_HOME']
        else:
            os.environ['XDG_CONFIG_HOME'] = self.old
        self.tmp.cleanup()

    def test_saved_and_read(self):
        self.assertEqual(runner_settings.load(), RunnerSettings())
        self.assertIsNone(runner_settings.stamp())
        runner_settings.save(RunnerSettings('en', 5))
        self.assertEqual(runner_settings.load(), RunnerSettings('en', 5))

    def test_prefix_and_interface(self):
        runner_settings.save(RunnerSettings(prefix='lat', interface='es'))
        s = runner_settings.load()
        self.assertEqual((s.prefix, s.interface), ('lat', 'es'))
        for wrong in ('', '  ', 'l a'):
            self.assertIsNone(runner_settings.good_prefix(wrong))
        with open(runner_settings.path(), 'w') as f:
            f.write('[runner]\nprefix = l a\n')
        self.assertEqual(runner_settings.load().prefix, 'pw')

    def test_the_dialogue_is_translated(self):
        """Each text of the settings window has its Spanish."""
        import ast
        import settings_dialog
        with open(os.path.join(HERE, 'settings_dialog.py')) as f:
            tree = ast.parse(f.read())
        used = {node.args[0].value for node in ast.walk(tree)
                if isinstance(node, ast.Call) and
                getattr(node.func, 'attr', '') == 't' and node.args and
                isinstance(node.args[0], ast.Constant)}
        used |= set(settings_dialog.INTERFACES.values())
        self.assertTrue(used)
        self.assertEqual(used - set(settings_dialog.TEXTS), set())

    def test_wrong_values(self):
        os.makedirs(os.path.dirname(runner_settings.path()))
        for text, results in (('results = many', 12), ('results = 0', 1),
                              ('results = 999', 50)):
            with open(runner_settings.path(), 'w') as f:
                f.write(f'[runner]\n{text}\n')
            self.assertEqual(runner_settings.load().results, results)

    @unittest.skipUnless(os.path.isdir(PY_WORDS), 'needs py-words next to it')
    def test_the_matches_follow_them(self):
        dictionary.use(PY_WORDS)
        words = dictionary.Dictionary()
        for code, meaning in (('en', 'love'), ('es', 'Amar')):
            runner_settings.save(RunnerSettings(code, 3))
            os.utime(runner_settings.path(), (0, len(code) + ord(code[1])))
            found = words.matches('amo')
            self.assertEqual(words.session.language.code, code)
            self.assertIn(meaning, found[0].subtext)
        runner_settings.save(RunnerSettings('', 1))
        os.utime(runner_settings.path(), (0, 1))
        self.assertEqual(len(words.matches('~e amo')), 1)


if __name__ == '__main__':
    unittest.main()
