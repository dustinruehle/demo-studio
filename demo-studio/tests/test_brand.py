"""brand.json is the single source. These tests pin the exact current output so
the refactor cannot restyle anything by accident."""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "shared"))

import brand  # noqa: E402

# The two guides diverge today. Pin both, deliberately.
FLOW_ACCENTS = {"amber": "#E0A100", "green": "#3B8C6E", "coral": "#E2664A"}
PG_ACCENTS = {"amber": "#B07A00", "green": "#2E7D5B", "coral": "#C0503A"}


class TestBrandTokens(unittest.TestCase):
    def test_core_tokens_are_shared(self):
        flow = brand.tokens("flow_guide")
        pg = brand.tokens("presenter_guide")
        for key in ("indigo", "ink", "paper", "card", "muted", "line"):
            with self.subTest(token=key):
                self.assertEqual(flow[key], pg[key], f"{key} must be shared core")
        self.assertEqual(flow["indigo"], "#4C2889")
        self.assertEqual(flow["ink"], "#1C1526")
        self.assertEqual(flow["paper"], "#F6F4FA")

    def test_surface_accents_stay_divergent(self):
        """Unifying these would restyle a guide. If this test ever needs changing,
        that is a deliberate design decision, not a refactor."""
        flow = brand.tokens("flow_guide")
        pg = brand.tokens("presenter_guide")
        for key, want in FLOW_ACCENTS.items():
            self.assertEqual(flow[key], want, f"flow_guide {key}")
        for key, want in PG_ACCENTS.items():
            self.assertEqual(pg[key], want, f"presenter_guide {key}")

    def test_unknown_surface_raises(self):
        with self.assertRaises(KeyError):
            brand.tokens("nope")

    def test_fonts_and_acts(self):
        self.assertEqual(brand.FONTS["heading"], "Fraunces")
        self.assertEqual(brand.FONTS["body"], "IBM Plex Sans")
        self.assertEqual(brand.FONTS["mono"], "JetBrains Mono")
        self.assertEqual(brand.acts()["Model"], "#4C2889")
        self.assertEqual(brand.acts()["Prove"], "#C0503A")

    def test_every_value_is_a_hex_colour(self):
        for surface in ("flow_guide", "presenter_guide", "pptx"):
            for key, value in brand.tokens(surface).items():
                with self.subTest(surface=surface, token=key):
                    self.assertRegex(value, r"^#[0-9A-F]{6}$",
                                     "store hex uppercase with a leading #")

    def test_pptx_surface_is_dark(self):
        pptx = brand.tokens("pptx")
        self.assertEqual(pptx["bg"], "#17131F")
        self.assertEqual(pptx["indigo"], "#8E6BE6")


class TestRootBlock(unittest.TestCase):
    def test_root_block_is_wellformed(self):
        css = brand.root_block("flow_guide")
        self.assertTrue(css.startswith(":root{"))
        self.assertTrue(css.rstrip().endswith("}"))
        self.assertIn("--indigo:#4C2889;", css)

    def test_root_block_contains_every_token(self):
        for surface in ("flow_guide", "presenter_guide"):
            css = brand.root_block(surface)
            for key, value in brand.tokens(surface).items():
                with self.subTest(surface=surface, token=key):
                    self.assertIn(f"--{key}:{value};", css)


class TestNoHexLiteralsRemain(unittest.TestCase):
    """After this task, colour lives in brand.json and nowhere else."""

    GENERATORS = [
        os.path.join(ROOT, "skills", "deck-flow-guide", "assets", "build_flow_guide.py"),
        os.path.join(ROOT, "skills", "presenter-guide", "assets", "build_presenter_guide.py"),
    ]

    def test_generators_contain_no_hex_literals(self):
        for path in self.GENERATORS:
            with self.subTest(path=os.path.basename(path)):
                with open(path) as f:
                    found = re.findall(r"#[0-9A-Fa-f]{6}\b", f.read())
                self.assertEqual(found, [],
                                 f"{os.path.basename(path)} still hardcodes {found}")


if __name__ == "__main__":
    unittest.main()
