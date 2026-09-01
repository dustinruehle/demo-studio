"""The plugin layout contract: manifest, skill dirs, frontmatter validity."""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

WORKERS = ["demo-studio", "demo-discovery", "build-spec",
           "deck-flow-guide", "create-slides", "presenter-guide"]


def frontmatter(path):
    with open(path) as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path}: no YAML frontmatter"
    return m.group(1)


class TestPluginLayout(unittest.TestCase):
    def test_manifest_exists_and_names_the_plugin(self):
        import json
        path = os.path.join(ROOT, ".claude-plugin", "plugin.json")
        self.assertTrue(os.path.exists(path), "missing .claude-plugin/plugin.json")
        with open(path) as f:
            manifest = json.load(f)
        self.assertEqual(manifest["name"], "demo-studio")
        self.assertIn("description", manifest)

    def test_every_skill_exists(self):
        for name in WORKERS:
            with self.subTest(skill=name):
                self.assertTrue(
                    os.path.exists(os.path.join(ROOT, "skills", name, "SKILL.md")),
                    f"missing skills/{name}/SKILL.md")

    def test_frontmatter_is_valid(self):
        for name in WORKERS:
            with self.subTest(skill=name):
                fm = frontmatter(os.path.join(ROOT, "skills", name, "SKILL.md"))
                got = re.search(r"^name: (\S+)$", fm, re.M)
                self.assertIsNotNone(got, f"{name}: no name field")
                self.assertEqual(got.group(1), name,
                                 f"{name}: frontmatter name must match the directory")
                self.assertRegex(got.group(1), r"^[a-z0-9-]+$",
                                 "name may use letters, numbers and hyphens only")
                self.assertLessEqual(len(fm), 1024,
                                     f"{name}: frontmatter is {len(fm)} chars, limit 1024")
                self.assertIn("description:", fm, f"{name}: no description field")

    def test_no_em_dashes_in_skills_or_shared(self):
        for base in ("skills", "shared"):
            for dirpath, _, files in os.walk(os.path.join(ROOT, base)):
                for fn in files:
                    if not fn.endswith((".md", ".py", ".js", ".json")):
                        continue
                    path = os.path.join(dirpath, fn)
                    with self.subTest(path=os.path.relpath(path, ROOT)):
                        with open(path) as f:
                            self.assertNotIn("—", f.read())


if __name__ == "__main__":
    unittest.main()
