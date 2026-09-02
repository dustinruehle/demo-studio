"""End to end: both generators build, on every supported interpreter, and their
output still matches the captured baseline."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASELINE = os.path.join(HERE, "baseline")

GENERATORS = [
    ("deck-flow-guide", "build_flow_guide.py", "flow_guide.example.json", "flow-guide.html"),
    ("presenter-guide", "build_presenter_guide.py", "presenter_guide.example.json", "presenter-guide.html"),
]


def run_generator(skill, script, config, out):
    """Run a generator. Returns (returncode, stdout, stderr)."""
    base = os.path.join(ROOT, "skills", skill, "assets")
    proc = subprocess.run(
        [sys.executable, os.path.join(base, script),
         os.path.join(base, "examples", config), out],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


class TestGeneratorsMatchBaseline(unittest.TestCase):
    def test_output_matches_baseline(self):
        for skill, script, config, golden in GENERATORS:
            with self.subTest(script=script):
                with tempfile.TemporaryDirectory() as tmp:
                    out = os.path.join(tmp, golden)
                    rc, _, err = run_generator(skill, script, config, out)
                    self.assertEqual(rc, 0, f"{script} failed: {err}")
                    with open(out) as f:
                        got = f.read()
                    with open(os.path.join(BASELINE, golden)) as f:
                        want = f.read()
                    self.assertEqual(got, want, f"{script} output drifted from baseline")


class TestNoEmDashes(unittest.TestCase):
    def test_generated_output_has_no_em_dashes(self):
        for _, _, _, golden in GENERATORS:
            with self.subTest(golden=golden):
                with open(os.path.join(BASELINE, golden)) as f:
                    self.assertNotIn("—", f.read())


class TestEmptyDiscoveryRecordIsNotSilentlySkipped(unittest.TestCase):
    """A discovery.json that reads back as `{}` was still loaded: the config
    named a real, readable file. The generator must report on it (an
    unresolved id hard-fails), not treat an empty record the same as no
    `discovery` field at all."""

    def test_a_traces_id_against_an_empty_discovery_record_hard_fails(self):
        base = os.path.join(ROOT, "skills", "deck-flow-guide", "assets")
        with open(os.path.join(base, "examples", "flow_guide.example.json")) as f:
            cfg = json.load(f)
        cfg["acts"][0]["cards"][0]["traces"] = "D99"
        with tempfile.TemporaryDirectory() as tmp:
            discovery_path = os.path.join(tmp, "discovery.json")
            with open(discovery_path, "w") as f:
                f.write("{}")
            cfg["discovery"] = discovery_path
            cfg_path = os.path.join(tmp, "flow_guide.json")
            with open(cfg_path, "w") as f:
                json.dump(cfg, f)
            out = os.path.join(tmp, "flow-guide.html")
            proc = subprocess.run(
                [sys.executable, os.path.join(base, "build_flow_guide.py"), cfg_path, out],
                capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0,
                                "an empty discovery record must not silently pass an unresolved id")
            self.assertIn("unresolved-trace", proc.stderr)
            self.assertIn("D99", proc.stderr)
            self.assertFalse(os.path.exists(out), "nothing should be written on a hard failure")


class TestInterpreterFloor(unittest.TestCase):
    """Both generators must parse and run on the 3.9 floor, not just 3.12."""

    INTERPRETERS = [p for p in ("/usr/bin/python3",
                                os.path.expanduser("~/.asdf/installs/python/3.12.12/bin/python3"))
                    if os.path.exists(p)]

    def test_generators_compile_on_every_interpreter(self):
        self.assertTrue(self.INTERPRETERS, "no interpreters found to test")
        for interp in self.INTERPRETERS:
            for skill, script, _, _ in GENERATORS:
                with self.subTest(interp=interp, script=script):
                    proc = subprocess.run(
                        [interp, "-m", "py_compile",
                         os.path.join(ROOT, "skills", skill, "assets", script)],
                        capture_output=True, text=True)
                    self.assertEqual(proc.returncode, 0,
                                     f"{script} does not compile on {interp}: {proc.stderr}")


if __name__ == "__main__":
    unittest.main()
