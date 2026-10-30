"""Exercise review extraction, output preservation and failure handling without model calls."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('review.sh').resolve()


class ReviewRunnerTests(unittest.TestCase):
    def test_runner(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            page = root / 'page.md'
            page.write_text('''# Test title

*Test subtitle.*

*Level 2 · navigation and status*

## Original drafting brief
SECRET_BRIEF

## Page copy (draft)
Visible explanation.

![Diagram description](diagram.svg)

<!-- SECRET_HISTORY -->
''')
            env = dict(os.environ, DRY_RUN='1')
            result = subprocess.run(['bash', str(SCRIPT), 'editorial', str(page), 'codex'],
                                    env=env, capture_output=True, text=True, check=True)
            for retained in ['# Test title', '*Test subtitle.*', 'Visible explanation.', 'Diagram description']:
                self.assertIn(retained, result.stdout)
            for excluded in ['SECRET_BRIEF', 'SECRET_HISTORY', 'navigation and status']:
                self.assertNotIn(excluded, result.stdout)
            self.assertFalse((root / '_authoring').exists())

            fake = root / 'codex'
            fake.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
sys.stdin.read()
if os.environ.get('FAKE_FAIL'): sys.exit(7)
assert '-s' in sys.argv and sys.argv[sys.argv.index('-s')+1] == 'read-only'
out = pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1])
out.write_text('A completed review.\\n')
''')
            fake.chmod(0o755)
            env.pop('DRY_RUN')
            env['CODEX_BIN'] = str(fake)
            command = ['bash', str(SCRIPT), 'editorial', str(page), 'codex']
            outputs = []
            for _ in range(2):
                result = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
                outputs.append(Path(result.stdout.strip()))
            self.assertNotEqual(*outputs)
            self.assertTrue(all('A completed review.' in p.read_text() for p in outputs))
            before = set((root / '_authoring').iterdir())
            env['FAKE_FAIL'] = '1'
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, set((root / '_authoring').iterdir()))

    def test_no_extension_uses_path_fallback(self):
        source = SCRIPT.read_text().split("CODEX_BIN=$(python3 - <<'PYCODE'\n", 1)[1].split('\nPYCODE', 1)[0]
        with tempfile.TemporaryDirectory() as folder:
            from contextlib import redirect_stdout
            from io import StringIO
            output = StringIO()
            with patch.object(Path, 'home', return_value=Path(folder)), redirect_stdout(output):
                exec(source, {})
            self.assertEqual(output.getvalue().strip(), 'codex')


if __name__ == '__main__':
    unittest.main()
