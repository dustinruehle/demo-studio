# demo-studio/tests/test_guardrails.py
"""Mechanical enforcement of the rules the skill previously only documented."""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

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


class TestMetaKeysNotSelfFlagged(unittest.TestCase):
    """Drives check_tree through the REAL generator call shape: banned_terms
    and allow_words are read off the same config object they are then used to
    walk, so both lists are also still keys inside that config. Without a
    skip, a banned term flags itself the moment it is declared, and the
    public-safe gate becomes unusable the moment anyone turns it on."""

    def test_banned_terms_key_does_not_flag_its_own_declaration(self):
        cfg = {"why": "as told by Contoso", "banned_terms": ["Contoso"]}
        found = g.check_tree(cfg, allowlist=cfg.get("allow_words", ()),
                              banned=cfg.get("banned_terms", ()))
        self.assertEqual([v.field for v in found], ["why"])

    def test_a_genuine_hit_elsewhere_in_the_config_still_fails(self):
        cfg = {"acts": [{"cards": [{"why": "Contoso told us this"}]}],
               "banned_terms": ["Contoso"]}
        found = g.check_tree(cfg, allowlist=cfg.get("allow_words", ()),
                              banned=cfg.get("banned_terms", ()))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].check, "public-safe")
        self.assertEqual(found[0].field, "acts[0].cards[0].why")

    def test_allow_words_key_does_not_flag_its_own_declaration(self):
        cfg = {"note": "a robust retry policy", "allow_words": ["robust"]}
        found = g.check_tree(cfg, allowlist=cfg.get("allow_words", ()),
                              banned=cfg.get("banned_terms", ()))
        self.assertEqual(found, [])


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

    def test_ai_tell_message_names_the_allow_words_escape(self):
        found = g.check_tree({"a": "a seamless pipeline"})
        with self.assertRaises(g.GuardrailError) as ctx:
            g.enforce(found)
        self.assertIn("allow_words", str(ctx.exception))

    def test_em_dash_only_message_does_not_mention_the_escape(self):
        """allow_words only escapes ai-tell hits; an em-dash-only failure has
        no allowlist to point at, so the message should not claim one."""
        found = g.check_tree({"a": "x — y"})
        with self.assertRaises(g.GuardrailError) as ctx:
            g.enforce(found)
        self.assertNotIn("allow_words", str(ctx.exception))


class TestPptxChecks(unittest.TestCase):
    FIXTURES = os.path.join(HERE, "fixtures", "make_bad_pptx.py")

    def _build(self, kind, path):
        subprocess.run([sys.executable, self.FIXTURES, kind, path], check=True)

    def _deck(self, path, body):
        """Write a one-slide deck whose spTree holds `body`."""
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("ppt/slides/slide1.xml",
                       '<?xml version="1.0" encoding="UTF-8"?>'
                       '<p:sld xmlns:p="http://schemas.openxmlformats.org/'
                       'presentationml/2006/main" xmlns:a="http://schemas.'
                       'openxmlformats.org/drawingml/2006/main">'
                       '<p:cSld><p:spTree>' + body + '</p:spTree></p:cSld></p:sld>')

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
            found = g.check_pptx(path)
            self.assertTrue(found, "check_pptx should find violations in bad fixture")
            self.assertTrue(all("slide1" in v.field for v in found))

    def test_a_clean_deck_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ok.pptx")
            self._build("clean", path)
            self.assertEqual(g.check_pptx(path), [])

    def test_slide_order_is_numeric_not_lexicographic(self):
        """A deck of eleven or more slides sorts slide10 ahead of slide2
        lexicographically. check_pptx must report findings in slide-number
        order, so a reader sees slide1, slide2, ..., slide11, not slide1,
        slide10, slide11, slide2, ..."""
        dash_slide = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
            '       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<p:cSld><p:spTree>'
            '<p:sp><p:spPr><a:ln><a:prstDash val="dash"/></a:ln></p:spPr></p:sp>'
            '</p:spTree></p:cSld></p:sld>'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "eleven.pptx")
            with zipfile.ZipFile(path, "w") as z:
                for n in range(1, 12):
                    z.writestr("ppt/slides/slide%d.xml" % n, dash_slide)
            found = g.check_pptx(path)
            fields = [v.field for v in found]
            expected = ["slide%d" % n for n in range(1, 12)]
            self.assertEqual(fields, expected)

    def test_flags_a_self_closing_connector(self):
        """The element patterns were anchored on `[ >]`, a space or the end of
        an opening tag. A shape carrying no children is written `<p:cxnSp/>`,
        which has neither, so the connector Google Slides drops walked
        straight through the gate that exists to catch it."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "selfclosing.pptx")
            self._deck(path, "<p:cxnSp/>")
            self.assertIn("pptx-connector", {v.check for v in g.check_pptx(path)})

    def test_flags_a_self_closing_dashed_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "selfclosingdash.pptx")
            self._deck(path, "<p:sp><p:spPr><a:ln><a:prstDash/></a:ln></p:spPr></p:sp>")
            self.assertIn("pptx-dash", {v.check for v in g.check_pptx(path)})

    def test_flags_a_single_quoted_connector_geometry(self):
        """XML attribute values are as valid in single quotes as in double.
        The geometry pattern only matched `prst="`, so any writer that quotes
        the other way produced a deck this gate called clean."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "singlequoted.pptx")
            self._deck(path, "<p:sp><p:spPr>"
                             "<a:prstGeom prst='straightConnector1'/>"
                             "</p:spPr></p:sp>")
            self.assertIn("pptx-connector", {v.check for v in g.check_pptx(path)})

    def test_widening_does_not_flag_neighbouring_names(self):
        """A '/' in the character class must not turn the patterns greedy.
        `<p:nvCxnSpPr/>` reads like the connector element and is not one, and
        `prst='rightArrow'` is the block arrow the guardrail tells authors to
        use instead of a connector."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "neighbours.pptx")
            self._deck(path, "<p:sp><p:nvCxnSpPr/><p:spPr>"
                             "<a:prstGeom prst='rightArrow'/>"
                             "<a:ln><a:solidFill/></a:ln>"
                             "</p:spPr></p:sp>")
            self.assertEqual(g.check_pptx(path), [])

    def test_non_zip_file_returns_unreadable_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "notazip.pptx")
            with open(path, "w") as f:
                f.write("this is not a zip file")
            found = g.check_pptx(path)
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].check, "pptx-unreadable")
            self.assertEqual(found[0].field, "notazip.pptx")


class TestGuardrailsCli(unittest.TestCase):
    """guardrails.py must be runnable standalone: the gate that cannot be
    bypassed by hand-editing a builder has to exist as a real command, not
    just as functions nothing calls."""

    GUARDRAILS = os.path.join(ROOT, "shared", "guardrails.py")
    FIXTURES = os.path.join(HERE, "fixtures", "make_bad_pptx.py")

    def test_usage_message_when_no_path_given(self):
        proc = subprocess.run([sys.executable, self.GUARDRAILS],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("usage", proc.stderr.lower())

    def test_exits_nonzero_and_reports_a_bad_deck(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.pptx")
            subprocess.run([sys.executable, self.FIXTURES, "bad", path], check=True)
            proc = subprocess.run([sys.executable, self.GUARDRAILS, path],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("pptx-connector", proc.stdout)

    def test_exits_zero_for_a_clean_deck(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ok.pptx")
            subprocess.run([sys.executable, self.FIXTURES, "clean", path], check=True)
            proc = subprocess.run([sys.executable, self.GUARDRAILS, path],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("clean", proc.stdout.lower())


if __name__ == "__main__":
    unittest.main()


class TestMetaKeyScoping(unittest.TestCase):
    """The meta-key exemption exists so banned_terms does not match itself. It
    must not reach a nested key that merely shares the name, which would be an
    unscannable hole in the gate."""

    def test_top_level_meta_keys_are_exempt(self):
        cfg = {"banned_terms": ["Contoso"], "why": "clean text"}
        self.assertEqual(g.check_tree(cfg, banned=cfg["banned_terms"]), [])

    def test_a_nested_key_of_the_same_name_is_still_scanned(self):
        cfg = {"session": {"banned_terms": "Contoso said seamless things"},
               "banned_terms": ["Contoso"]}
        checks = {v.check for v in g.check_tree(cfg, banned=cfg["banned_terms"])}
        self.assertIn("public-safe", checks)
        self.assertIn("ai-tell", checks)

    def test_a_nested_allow_words_is_still_scanned(self):
        cfg = {"fork": {"allow_words": "a seamless choice"}}
        self.assertIn("ai-tell", {v.check for v in g.check_tree(cfg)})
