"""End to end: both generators build, on every supported interpreter, and their
output still matches the captured baseline."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASELINE = os.path.join(HERE, "baseline")

GENERATORS = [
    ("build_flow_guide.py", "flow_guide.example.json", "flow-guide.html"),
    ("build_presenter_guide.py", "presenter_guide.example.json", "presenter-guide.html"),
]


def run_generator(script, config, out):
    """Run a generator. Returns (returncode, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "assets", script),
         os.path.join(ROOT, "assets", "examples", config), out],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


class TestGeneratorsMatchBaseline(unittest.TestCase):
    def test_output_matches_baseline(self):
        for script, config, golden in GENERATORS:
            with self.subTest(script=script):
                with tempfile.TemporaryDirectory() as tmp:
                    out = os.path.join(tmp, golden)
                    rc, _, err = run_generator(script, config, out)
                    self.assertEqual(rc, 0, f"{script} failed: {err}")
                    with open(out) as f:
                        got = f.read()
                    with open(os.path.join(BASELINE, golden)) as f:
                        want = f.read()
                    self.assertEqual(got, want, f"{script} output drifted from baseline")


class TestNoEmDashes(unittest.TestCase):
    def test_generated_output_has_no_em_dashes(self):
        for _, _, golden in GENERATORS:
            with self.subTest(golden=golden):
                with open(os.path.join(BASELINE, golden)) as f:
                    self.assertNotIn("—", f.read())


if __name__ == "__main__":
    unittest.main()
