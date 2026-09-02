"""Descriptions are the discovery interface. Guard the rules that make them work."""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILLS = os.path.join(ROOT, "skills")

WORKERS = ["demo-discovery", "build-spec", "deck-flow-guide",
           "create-slides", "presenter-guide"]
ALL = ["demo-studio"] + WORKERS

# Phrases that describe HOW a skill works rather than WHEN to use it. A
# description that summarizes a workflow gets followed instead of the skill body.
WORKFLOW_TELLS = ("first ", "then ", "step 1", "stage 1", "followed by",
                  "and then", "after that")


def description(name):
    path = os.path.join(SKILLS, name, "SKILL.md")
    with open(path) as f:
        text = f.read()
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1)
    body = fm.split("description:", 1)[1]
    body = body.lstrip(">|-\n ")
    body = body.split("\nname:")[0]
    return " ".join(line.strip() for line in body.strip().splitlines())


class TestDescriptions(unittest.TestCase):
    def test_each_description_states_when_to_use_it(self):
        for name in ALL:
            with self.subTest(skill=name):
                self.assertIn("use when", description(name).lower(),
                              f"{name}: description must state triggering conditions")

    def test_no_description_summarizes_a_workflow(self):
        for name in ALL:
            desc = description(name).lower()
            for tell in WORKFLOW_TELLS:
                with self.subTest(skill=name, tell=tell):
                    self.assertNotIn(tell, desc,
                                     f"{name}: description reads like a workflow summary")

    def test_worker_descriptions_name_their_artifact(self):
        expected = {
            "demo-discovery": ["transcript", "demo fit"],
            "build-spec": ["build spec"],
            "deck-flow-guide": ["flow guide"],
            "create-slides": ["slides"],
            "presenter-guide": ["presenter guide"],
        }
        for name, needles in expected.items():
            desc = description(name).lower()
            for needle in needles:
                with self.subTest(skill=name, needle=needle):
                    self.assertIn(needle, desc)

    def test_the_router_does_not_claim_the_workers_artifacts(self):
        """If the router advertises 'presenter guide', a direct request for one
        may match the router instead of the worker that builds it."""
        router = description("demo-studio").lower()
        for claimed in ("presenter guide", "flow guide", "build spec"):
            with self.subTest(claimed=claimed):
                self.assertNotIn(claimed, router)

    def test_the_router_and_demo_discovery_do_not_both_claim_a_bare_transcript_share(self):
        """A bare transcript share ("here's the transcript from our call") is the
        router's job: its own entry table routes that phrase onward through the
        whole pipeline. demo-discovery must not also fire on that same unqualified
        ask, or a selector match can land the pipeline at stage 1 in isolation
        when the user wanted the whole set."""
        router = description("demo-studio").lower()
        discovery = description("demo-discovery").lower()
        self.assertIn("transcript", router,
                      "the router should own the bare transcript-share trigger")
        self.assertIn("transcript", discovery,
                      "demo-discovery should still anchor on transcripts for its narrower ask")
        self.assertIn("without asking for the rest of the pipeline", discovery,
                      "demo-discovery must exclude the full-pipeline ask that the router "
                      "owns, or a bare transcript share can match here instead of the router")

    def test_the_router_claims_a_multi_artifact_or_resume_partway_request(self):
        """"I know the demo already, build the deck and the guides" names three
        artifacts. If the router only excludes single-artifact requests without
        positively claiming this case, a single worker can win it on a keyword
        match and the router never gets a chance to sequence the workers."""
        router = description("demo-studio").lower()
        self.assertTrue(
            any(phrase in router for phrase in
                ("several pieces", "resume the pipeline", "partway")),
            "router description must positively claim a multi-artifact or "
            "resume-partway request, not rely on vagueness")

    # The frontmatter 1024-char budget is already covered by
    # test_layout.TestPluginLayout.test_frontmatter_is_valid; no need to
    # duplicate it here.

    def test_the_router_names_workers_without_at_links(self):
        """@ links force-load files and burn context."""
        with open(os.path.join(SKILLS, "demo-studio", "SKILL.md")) as f:
            body = f.read()
        self.assertNotIn("@skills/", body)
        for worker in WORKERS:
            with self.subTest(worker=worker):
                # The bare name, not a namespace-prefixed one. A plugin install
                # addresses these as demo-studio:<worker> and a personal skills
                # directory addresses them as <worker>; the router must read
                # correctly under both, so it names the identity and lets the
                # prefix resolve.
                self.assertIn(f"`{worker}`", body)
        self.assertNotIn("demo-studio:demo-discovery", body,
                         "the router must not hardcode one install method's prefix")


if __name__ == "__main__":
    unittest.main()
