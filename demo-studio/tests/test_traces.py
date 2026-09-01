"""traces-to stops being an honour system."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "shared"))

import traces  # noqa: E402

DISCOVERY = {"engagement": "x", "signals": [
    {"id": "D1", "kind": "grounded", "text": "a", "quote": "q", "attribution": "r"},
    {"id": "D2", "kind": "inferred", "text": "b"},
]}


class TestRefs(unittest.TestCase):
    def test_finds_ids_in_prose(self):
        self.assertEqual(traces.refs("traces to D1 and D2"), ["D1", "D2"])

    def test_deduplicates_preserving_order(self):
        self.assertEqual(traces.refs("D2 then D1 then D2"), ["D2", "D1"])

    def test_ignores_lookalikes(self):
        self.assertEqual(traces.refs("D1A and XD2 and D and 1D"), [])

    def test_finds_ids_inside_html(self):
        self.assertEqual(traces.refs("<b>D1</b> drove this"), ["D1"])

    def test_returns_empty_for_prose_with_no_ids(self):
        self.assertEqual(traces.refs("the platform lead said so"), [])


class TestSignalIds(unittest.TestCase):
    def test_collects_every_id(self):
        self.assertEqual(traces.signal_ids(DISCOVERY), {"D1", "D2"})


class TestCheckTraces(unittest.TestCase):
    def test_a_resolvable_trace_passes(self):
        cfg = {"acts": [{"cards": [{"traces": "D1"}]}]}
        self.assertEqual(traces.check_traces(cfg, DISCOVERY), [])

    def test_an_unresolvable_id_is_reported_with_its_path(self):
        cfg = {"acts": [{"cards": [{"traces": "D9"}]}]}
        found = traces.check_traces(cfg, DISCOVERY)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].check, "unresolved-trace")
        self.assertEqual(found[0].field, "acts[0].cards[0].traces")
        self.assertIn("D9", found[0].detail)

    def test_free_text_traces_are_reported_as_untraced(self):
        cfg = {"acts": [{"cards": [{"traces": "the security architect said so"}]}]}
        found = traces.check_traces(cfg, DISCOVERY)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].check, "untraced")

    def test_only_traces_fields_are_inspected(self):
        cfg = {"acts": [{"cards": [{"why": "D9 is great", "traces": "D1"}]}]}
        self.assertEqual(traces.check_traces(cfg, DISCOVERY), [])

    def test_presenter_guide_shape_is_walked_too(self):
        cfg = {"slides": [{"num": 1, "traces": "D2"}, {"num": 2, "traces": "D7"}]}
        found = traces.check_traces(cfg, DISCOVERY)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].field, "slides[1].traces")

    def test_several_ids_in_one_field_are_each_resolved(self):
        cfg = {"acts": [{"cards": [{"traces": "D1 and D9 and D2"}]}]}
        found = traces.check_traces(cfg, DISCOVERY)
        self.assertEqual([v.detail for v in found].count("D9 does not exist"), 1)

    def test_no_discovery_means_no_checking(self):
        cfg = {"acts": [{"cards": [{"traces": "D9"}]}]}
        self.assertEqual(traces.check_traces(cfg, None), [])


if __name__ == "__main__":
    unittest.main()
