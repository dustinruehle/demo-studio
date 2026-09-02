"""The presenter-guide config rules the schema dialect cannot express."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "skills", "presenter-guide", "assets")
sys.path.insert(0, os.path.join(ROOT, "shared"))
sys.path.insert(0, ASSETS)

import validate_config as vc  # noqa: E402
import build_presenter_guide as bpg  # noqa: E402

EXAMPLE = os.path.join(ASSETS, "examples", "presenter_guide.example.json")
SCRIPT = os.path.join(ASSETS, "build_presenter_guide.py")


def load_example():
    with open(EXAMPLE) as f:
        return json.load(f)


class TestActsShape(unittest.TestCase):
    """`acts` is declared only as {"type": "object"}: the dialect can say the
    field is a map, not that its values are `[label, "#RRGGBB"]` pairs. build()
    indexes v[0] and v[1] straight out of whatever is there, so a string value
    yielded its first two characters and put `style="color:n"` on the page.
    The act colouring was silently gone, with nothing raised, nothing written
    to stderr, and nothing an author could grep for.
    """

    def reject(self, acts):
        """Run check_acts against a mutated acts map, return the message."""
        cfg = load_example()
        cfg["acts"] = acts
        with self.assertRaises(vc.ConfigError) as caught:
            bpg.check_acts(cfg)
        return str(caught.exception)

    def test_the_example_acts_pass(self):
        bpg.check_acts(load_example())

    def test_a_string_instead_of_a_label_colour_pair_is_rejected(self):
        message = self.reject({k: "indigo" for k in load_example()["acts"]})
        self.assertIn("acts.Open", message)
        self.assertIn("'indigo'", message)

    def test_a_one_element_act_is_rejected_not_an_index_error(self):
        acts = load_example()["acts"]
        acts["Open"] = ["Open"]
        self.assertIn("acts.Open", self.reject(acts))

    def test_a_null_act_is_rejected(self):
        acts = load_example()["acts"]
        acts["Open"] = None
        self.assertIn("acts.Open", self.reject(acts))

    def test_a_colour_that_is_not_hex_is_rejected(self):
        acts = load_example()["acts"]
        acts["Open"] = ["Open", "red"]
        message = self.reject(acts)
        self.assertIn("acts.Open", message)
        self.assertIn("hex", message)

    def test_a_hex_colour_missing_its_leading_hash_is_rejected(self):
        """The PPTX backend wants bare hex, this one lands in a CSS style
        attribute and needs the '#'. An author moving between the two writes
        the wrong one, and `color:1C1526` is not a colour."""
        acts = load_example()["acts"]
        acts["Open"] = ["Open", "1C1526"]
        self.assertIn("acts.Open", self.reject(acts))

    def test_a_blank_label_is_rejected(self):
        acts = load_example()["acts"]
        acts["Open"] = ["   ", "#1C1526"]
        self.assertIn("acts.Open", self.reject(acts))

    def test_every_bad_act_is_reported_not_just_the_first(self):
        acts = load_example()["acts"]
        acts["Open"] = "indigo"
        acts["Frame"] = ["Frame", "red"]
        message = self.reject(acts)
        self.assertIn("acts.Open", message)
        self.assertIn("acts.Frame", message)

    def test_a_slide_act_that_is_not_a_key_in_acts_is_rejected(self):
        cfg = load_example()
        cfg["slides"][0]["act"] = "Nope"
        with self.assertRaises(vc.ConfigError) as caught:
            bpg.check_acts(cfg)
        self.assertIn("slides[0].act", str(caught.exception))


class TestMalformedActsIsACleanFailure(unittest.TestCase):
    def test_a_string_act_fails_the_build_instead_of_rendering_color_n(self):
        cfg = load_example()
        cfg["acts"] = {k: "indigo" for k in cfg["acts"]}
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = os.path.join(tmp, "presenter_guide.json")
            with open(cfg_path, "w") as f:
                json.dump(cfg, f)
            out = os.path.join(tmp, "presenter-guide.html")
            proc = subprocess.run([sys.executable, SCRIPT, cfg_path, out],
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0,
                                "a malformed acts map must not build")
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn("acts.Open", proc.stderr)
            self.assertFalse(os.path.exists(out),
                             "nothing should be written on a hard failure")


if __name__ == "__main__":
    unittest.main()
