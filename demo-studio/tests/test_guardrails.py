# demo-studio/tests/test_guardrails.py
"""Mechanical enforcement of the rules the skill previously only documented."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "shared"))

import guardrails as g  # noqa: E402


class TestEmDash(unittest.TestCase):
    def test_flags_an_em_dash_and_names_the_field(self):
        found = g.check_text("durable execution — done right", "slides[0].title")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].check, "em-dash")
        self.assertEqual(found[0].field, "slides[0].title")

    def test_accepts_a_hyphen_and_an_en_dash(self):
        self.assertEqual(g.check_text("well-known", "f"), [])
        self.assertEqual(g.check_text("pages 3-9", "f"), [])


class TestAiTells(unittest.TestCase):
    def test_flags_filler_and_names_the_word(self):
        found = g.check_text("a seamless and robust pipeline", "why")
        words = sorted(v.detail for v in found)
        self.assertEqual(words, ["robust", "seamless"])
        self.assertTrue(all(v.check == "ai-tell" for v in found))

    def test_matches_whole_words_only(self):
        """'actually' is a tell; 'actual' is an ordinary word."""
        self.assertEqual(g.check_text("the actual throughput", "f"), [])
        self.assertEqual(len(g.check_text("actually, it works", "f")), 1)

    def test_is_case_insensitive(self):
        self.assertEqual(len(g.check_text("Leverage the queue", "f")), 1)

    def test_allowlist_permits_a_legitimate_use(self):
        found = g.check_text("the robust mode flag", "f", allowlist=("robust",))
        self.assertEqual(found, [])


class TestPublicSafe(unittest.TestCase):
    def test_flags_a_banned_identifier(self):
        found = g.check_text("as Contoso told us", "why", )
        self.assertEqual(found, [])  # no banned list supplied, so nothing to flag
        found = g.check_tree({"why": "as Contoso told us"}, banned=("Contoso",))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].check, "public-safe")
        self.assertEqual(found[0].field, "why")

    def test_banned_matching_is_word_bounded_and_case_insensitive(self):
        self.assertEqual(len(g.check_tree({"a": "CONTOSO"}, banned=("Contoso",))), 1)
        self.assertEqual(g.check_tree({"a": "Contosoville"}, banned=("Contoso",)), [])

    def test_symbol_edged_banned_terms_are_flagged(self):
        """A banned term whose own edge character is non-word (C++, Yahoo!,
        a bracketed form) must still be caught: \\b requires a word/non-word
        transition, which cannot happen at an edge that is already non-word."""
        self.assertEqual(len(g.check_tree({"a": "we used C++ for this"}, banned=("C++",))), 1)
        self.assertEqual(len(g.check_tree({"a": "a Yahoo! account"}, banned=("Yahoo!",))), 1)
        self.assertEqual(len(g.check_tree({"a": "look at (x) here"}, banned=("(x)",))), 1)

    def test_contosoville_still_not_flagged_after_symbol_fix(self):
        """Regression guard: fixing the symbol-edge bug must not loosen the
        match into a substring match. Contoso must still not match inside
        Contosoville."""
        self.assertEqual(g.check_tree({"a": "Contosoville"}, banned=("Contoso",)), [])


class TestTreeWalk(unittest.TestCase):
    def test_builds_dotted_paths_through_dicts_and_lists(self):
        cfg = {"acts": [{"cards": [{"why": "a — b"}]}]}
        found = g.check_tree(cfg)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].field, "acts[0].cards[0].why")

    def test_checks_dict_keys_are_ignored_but_values_are_not(self):
        found = g.check_tree({"title": "fine", "sub": "not — fine"})
        self.assertEqual([v.field for v in found], ["sub"])

    def test_non_string_scalars_are_skipped(self):
        self.assertEqual(g.check_tree({"n": 3, "b": True, "z": None}), [])


class TestEnforce(unittest.TestCase):
    def test_enforce_is_a_no_op_when_clean(self):
        g.enforce([])  # must not raise

    def test_enforce_raises_and_the_message_names_every_field(self):
        found = g.check_tree({"a": "x — y", "b": "seamless"})
        with self.assertRaises(g.GuardrailError) as ctx:
            g.enforce(found)
        message = str(ctx.exception)
        self.assertIn("a", message)
        self.assertIn("b", message)

    def test_report_is_one_line_per_violation(self):
        found = g.check_tree({"a": "x — y", "b": "seamless"})
        self.assertEqual(len(g.report(found).strip().splitlines()), 2)


class TestPptxChecks(unittest.TestCase):
    FIXTURES = os.path.join(HERE, "fixtures", "make_bad_pptx.py")

    def _build(self, kind, path):
        subprocess.run([sys.executable, self.FIXTURES, kind, path], check=True)

    def test_flags_a_line_connector(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.pptx")
            self._build("bad", path)
            found = g.check_pptx(path)
            checks = {v.check for v in found}
            self.assertIn("pptx-connector", checks)

    def test_flags_a_dashed_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.pptx")
            self._build("bad", path)
            self.assertIn("pptx-dash", {v.check for v in g.check_pptx(path)})

    def test_names_the_offending_slide(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.pptx")
            self._build("bad", path)
            self.assertTrue(all("slide1" in v.field for v in g.check_pptx(path)))

    def test_a_clean_deck_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ok.pptx")
            self._build("clean", path)
            self.assertEqual(g.check_pptx(path), [])


if __name__ == "__main__":
    unittest.main()
