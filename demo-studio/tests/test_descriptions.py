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

    def test_every_description_fits_the_frontmatter_budget(self):
        for name in ALL:
            with self.subTest(skill=name):
                path = os.path.join(SKILLS, name, "SKILL.md")
                with open(path) as f:
                    fm = re.match(r"^---\n(.*?)\n---\n", f.read(), re.S).group(1)
                self.assertLessEqual(len(fm), 1024, f"{name}: {len(fm)} chars")

    def test_the_router_names_workers_without_at_links(self):
        """@ links force-load files and burn context."""
        with open(os.path.join(SKILLS, "demo-studio", "SKILL.md")) as f:
            body = f.read()
        self.assertNotIn("@skills/", body)
        for worker in WORKERS:
            with self.subTest(worker=worker):
                self.assertIn(f"demo-studio:{worker}", body)


if __name__ == "__main__":
    unittest.main()
