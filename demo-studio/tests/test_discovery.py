"""The discovery artifact: schema, id rules, and the readable render."""
import json
import os
import re
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

    def test_an_empty_quote_is_caught_by_the_schema(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["quote"] = ""
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("quote" in e for e in errors), errors)

    def test_an_empty_attribution_is_caught_by_the_schema(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["attribution"] = ""
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("attribution" in e for e in errors), errors)

    def test_a_null_allow_word_is_a_clean_schema_error_not_a_crash(self):
        """The other two schemas (flow-guide, presenter-guide) already declare
        allow_words/banned_terms as arrays of strings; this one did not, so a
        null slipped past validation and blew up later inside guardrails with
        a raw AttributeError on None.lower(). Declaring the field here lets
        the schema walker catch it first, the same clean-message contract
        every other bad field in this config honours."""
        cfg = load_example()
        cfg["allow_words"] = [None]
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("allow_words[0]" in e for e in errors), errors)

    def test_a_null_banned_term_is_a_clean_schema_error(self):
        cfg = load_example()
        cfg["banned_terms"] = [None]
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("banned_terms[0]" in e for e in errors), errors)


class TestSignalRules(unittest.TestCase):
    def test_ids_are_unique(self):
        cfg = load_example()
        cfg["signals"].append(dict(cfg["signals"][0]))
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_ids_match_the_expected_shape(self):
        cfg = load_example()
        # D4 and D5 are inferred signals that nothing else names in an
        # "exercises" list. Mutating one of those isolates the ID_RE check:
        # renaming a referenced id (like D1) also trips the exercises
        # reference check independently, which would let this test pass even
        # with the ID_RE branch deleted.
        unreferenced = cfg["signals"][4]
        self.assertEqual(unreferenced["id"], "D5")
        unreferenced["id"] = "sig-1"
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("sig-1", str(ctx.exception))
        self.assertIn("must look like", str(ctx.exception))

    def test_a_leading_zero_id_is_rejected(self):
        cfg = load_example()
        unreferenced = cfg["signals"][4]
        self.assertEqual(unreferenced["id"], "D5")
        unreferenced["id"] = "D01"
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("D01", str(ctx.exception))

    def test_d_zero_is_rejected(self):
        cfg = load_example()
        cfg["signals"][4]["id"] = "D0"
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("D0", str(ctx.exception))

    def test_double_digit_ids_are_accepted(self):
        cfg = load_example()
        cfg["signals"][4]["id"] = "D10"
        build_discovery.check_signals(cfg)  # must not raise

    def test_a_grounded_signal_must_carry_a_quote_and_attribution(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        del grounded["quote"]
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("quote", str(ctx.exception))

    def test_an_empty_quote_is_rejected(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["quote"] = ""
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("quote", str(ctx.exception))

    def test_a_whitespace_only_quote_is_rejected(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["quote"] = "   "
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("quote", str(ctx.exception))

    def test_a_tab_only_quote_is_rejected(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["quote"] = "\t"
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("quote", str(ctx.exception))

    def test_an_empty_attribution_is_rejected(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["attribution"] = ""
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("attribution", str(ctx.exception))

    def test_a_whitespace_only_attribution_is_rejected(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["attribution"] = "   "
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("attribution", str(ctx.exception))

    def test_a_tab_only_attribution_is_rejected(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        grounded["attribution"] = "\t"
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("attribution", str(ctx.exception))

    def test_a_legitimate_grounded_signal_still_passes(self):
        cfg = load_example()
        build_discovery.check_signals(cfg)  # must not raise

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

    def test_a_pipe_in_a_demo_fit_cell_does_not_corrupt_the_row(self):
        cfg = load_example()
        cfg["demo_fit"][0]["why"] = "shows D1 | or does it"
        md = build_discovery.render(cfg)
        row = next(line for line in md.splitlines()
                   if line.startswith("| " + cfg["demo_fit"][0]["demo"]))
        self.assertIn("\\|", row)
        # A true column boundary is a "|" not preceded by a backslash. A
        # 3-column row has exactly 4: leading, two internal, trailing.
        boundaries = re.findall(r"(?<!\\)\|", row)
        self.assertEqual(len(boundaries), 4, row)

    def test_a_pipe_in_a_beats_cell_does_not_corrupt_the_row(self):
        cfg = load_example()
        cfg["session"]["beats"][0][1] = "Open and frame | orient"
        md = build_discovery.render(cfg)
        row = next(line for line in md.splitlines() if line.startswith("| 00:00"))
        self.assertIn("\\|", row)
        boundaries = re.findall(r"(?<!\\)\|", row)
        self.assertEqual(len(boundaries), 4, row)

    def test_cli_writes_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "discovery.md")
            proc = subprocess.run(
                [sys.executable, os.path.join(ASSETS, "build_discovery.py"), EXAMPLE, out],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.exists(out))

    def test_cli_with_no_arguments_prints_usage_not_a_traceback(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(ASSETS, "build_discovery.py")],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("usage", proc.stderr.lower())
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
