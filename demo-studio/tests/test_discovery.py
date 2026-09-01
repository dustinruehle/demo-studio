"""The discovery artifact: schema, id rules, and the readable render."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "skills", "demo-discovery", "assets")
sys.path.insert(0, os.path.join(ROOT, "shared"))
sys.path.insert(0, ASSETS)

import validate_config as vc  # noqa: E402
import schema_discovery  # noqa: E402
import build_discovery  # noqa: E402

EXAMPLE = os.path.join(ASSETS, "examples", "discovery.example.json")


def load_example():
    with open(EXAMPLE) as f:
        return json.load(f)


class TestSchema(unittest.TestCase):
    def test_the_example_validates(self):
        self.assertEqual(vc.validate(load_example(), schema_discovery.SCHEMA), [])

    def test_a_signal_needs_an_id_and_a_kind(self):
        cfg = load_example()
        del cfg["signals"][0]["kind"]
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("signals[0].kind" in e for e in errors), errors)

    def test_kind_is_restricted(self):
        cfg = load_example()
        cfg["signals"][0]["kind"] = "maybe"
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("grounded" in e for e in errors), errors)


class TestSignalRules(unittest.TestCase):
    def test_ids_are_unique(self):
        cfg = load_example()
        cfg["signals"].append(dict(cfg["signals"][0]))
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_ids_match_the_expected_shape(self):
        cfg = load_example()
        cfg["signals"][0]["id"] = "sig-1"
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("D1", str(ctx.exception))

    def test_a_grounded_signal_must_carry_a_quote_and_attribution(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        del grounded["quote"]
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("quote", str(ctx.exception))

    def test_an_inferred_signal_needs_no_quote(self):
        cfg = load_example()
        inferred = [s for s in cfg["signals"] if s["kind"] == "inferred"]
        self.assertTrue(inferred, "the example must include an inferred signal")
        build_discovery.check_signals(cfg)  # must not raise

    def test_exercises_must_reference_real_signals(self):
        cfg = load_example()
        inferred = next(s for s in cfg["signals"] if s["kind"] == "inferred")
        inferred["exercises"] = ["D99"]
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("D99", str(ctx.exception))


class TestRender(unittest.TestCase):
    def test_renders_markdown_naming_every_signal(self):
        cfg = load_example()
        md = build_discovery.render(cfg)
        for signal in cfg["signals"]:
            self.assertIn(signal["id"], md)

    def test_grounded_and_inferred_are_visibly_separated(self):
        md = build_discovery.render(load_example())
        self.assertIn("GROUNDED", md.upper())
        self.assertIn("INFERRED", md.upper())

    def test_no_em_dashes_in_the_render(self):
        self.assertNotIn("—", build_discovery.render(load_example()))

    def test_cli_writes_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "discovery.md")
            proc = subprocess.run(
                [sys.executable, os.path.join(ASSETS, "build_discovery.py"), EXAMPLE, out],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
