"""Config errors must name the path, not raise a traceback."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "shared"))

import validate_config as vc  # noqa: E402

CARD = {
    "type": "object",
    "required": ["type", "seq", "title"],
    "properties": {
        "type": {"type": "string", "enum": ["deck", "create"]},
        "seq": {"type": "number"},
        "title": {"type": "string", "minLength": 1},
    },
}
SCHEMA = {
    "type": "object",
    "required": ["title", "acts"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "acts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["no", "cards"],
                "properties": {
                    "no": {"type": "number"},
                    "cards": {"type": "array", "items": CARD},
                },
            },
        },
    },
}

GOOD = {"title": "T", "acts": [{"no": 1, "cards": [
    {"type": "deck", "seq": 1, "title": "A"}]}]}


class TestValidate(unittest.TestCase):
    def test_a_valid_config_produces_no_errors(self):
        self.assertEqual(vc.validate(GOOD, SCHEMA), [])

    def test_extra_keys_are_permitted(self):
        cfg = dict(GOOD, unknown_future_field=1)
        self.assertEqual(vc.validate(cfg, SCHEMA), [])

    def test_missing_top_level_required_field(self):
        cfg = {"acts": []}
        errors = vc.validate(cfg, SCHEMA, name="flow_guide.json")
        self.assertEqual(len(errors), 1)
        self.assertIn("flow_guide.json", errors[0])
        self.assertIn("title", errors[0])
        self.assertIn("required", errors[0])

    def test_missing_nested_required_field_names_the_index(self):
        cfg = {"title": "T", "acts": [{"no": 1, "cards": [{"type": "deck", "seq": 1}]}]}
        errors = vc.validate(cfg, SCHEMA)
        self.assertEqual(len(errors), 1)
        self.assertIn("acts[0].cards[0].title", errors[0])

    def test_wrong_type_names_the_path_and_both_types(self):
        cfg = {"title": 42, "acts": []}
        errors = vc.validate(cfg, SCHEMA)
        self.assertEqual(len(errors), 1)
        self.assertIn("title", errors[0])
        self.assertIn("string", errors[0])
        self.assertIn("number", errors[0])

    def test_enum_violation_lists_the_permitted_values(self):
        cfg = {"title": "T", "acts": [{"no": 1, "cards": [
            {"type": "slide", "seq": 1, "title": "A"}]}]}
        errors = vc.validate(cfg, SCHEMA)
        self.assertEqual(len(errors), 1)
        self.assertIn("acts[0].cards[0].type", errors[0])
        self.assertIn("deck", errors[0])
        self.assertIn("create", errors[0])

    def test_empty_string_fails_minlength(self):
        cfg = {"title": "", "acts": []}
        errors = vc.validate(cfg, SCHEMA)
        self.assertEqual(len(errors), 1)
        self.assertIn("title", errors[0])

    def test_every_error_is_reported_not_just_the_first(self):
        cfg = {"acts": [{"cards": []}]}
        errors = vc.validate(cfg, SCHEMA)
        self.assertGreaterEqual(len(errors), 2)

    def test_array_given_an_object_reports_cleanly(self):
        cfg = {"title": "T", "acts": {"no": 1}}
        errors = vc.validate(cfg, SCHEMA)
        self.assertEqual(len(errors), 1)
        self.assertIn("acts", errors[0])


class TestEnforce(unittest.TestCase):
    def test_enforce_passes_a_valid_config(self):
        vc.enforce(GOOD, SCHEMA)

    def test_enforce_raises_config_error_listing_every_problem(self):
        with self.assertRaises(vc.ConfigError) as ctx:
            vc.enforce({"acts": [{"cards": []}]}, SCHEMA, name="f.json")
        self.assertIn("f.json", str(ctx.exception))


class TestRealSchemas(unittest.TestCase):
    """The shipped example configs must satisfy their own schemas."""

    def test_flow_guide_example_validates(self):
        import json
        sys.path.insert(0, os.path.join(ROOT, "skills", "deck-flow-guide", "assets"))
        import schema_flow_guide
        path = os.path.join(ROOT, "skills", "deck-flow-guide", "assets",
                            "examples", "flow_guide.example.json")
        with open(path) as f:
            self.assertEqual(vc.validate(json.load(f), schema_flow_guide.SCHEMA), [])

    def test_presenter_guide_example_validates(self):
        import json
        sys.path.insert(0, os.path.join(ROOT, "skills", "presenter-guide", "assets"))
        import schema_presenter_guide
        path = os.path.join(ROOT, "skills", "presenter-guide", "assets",
                            "examples", "presenter_guide.example.json")
        with open(path) as f:
            self.assertEqual(vc.validate(json.load(f), schema_presenter_guide.SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
