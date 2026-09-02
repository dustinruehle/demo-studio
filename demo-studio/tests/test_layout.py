"""The plugin layout contract: manifest, skill dirs, frontmatter validity."""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)

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

    def test_the_marketplace_manifest_lists_the_plugin(self):
        import json
        path = os.path.join(REPO, ".claude-plugin", "marketplace.json")
        self.assertTrue(os.path.exists(path),
                        "missing .claude-plugin/marketplace.json, the repo is "
                        "not installable as a marketplace without it")
        with open(path) as f:
            manifest = json.load(f)
        entries = {p["name"]: p["source"] for p in manifest["plugins"]}
        self.assertEqual(entries.get("demo-studio"), "./demo-studio")

    def test_the_documented_install_commands_are_real(self):
        """The install block sat on `<owner>/<repo>` through a merge, and the
        marketplace name it installs from lives in a different file. Both are
        the first thing a reader runs, and neither is exercised by anything
        else, so they are checked here against the manifest."""
        import json
        with open(os.path.join(REPO, ".claude-plugin", "marketplace.json")) as f:
            marketplace = json.load(f)
        with open(os.path.join(REPO, "README.md")) as f:
            readme = f.read()
        add = re.search(r"claude plugin marketplace add (\S+)", readme)
        install = re.search(r"claude plugin install (\S+)@(\S+)", readme)
        self.assertTrue(add and install, "README documents no install commands")
        slug = add.group(1)
        self.assertRegex(slug, r"^[\w.-]+/[\w.-]+$",
                         "marketplace add names a placeholder, not a real repo")
        plugin, market = install.group(1), install.group(2)
        self.assertEqual(market, marketplace["name"],
                         "README installs from a marketplace name the manifest "
                         "does not declare")
        self.assertIn(plugin, {p["name"] for p in marketplace["plugins"]})

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
        # guardrails.py and lint_slides.js both spell EM_DASH as an escape
        # sequence, not a literal character, so no exemption is needed here:
        # an exact-string exemption silently stops guarding the moment
        # anyone reformats the exempted line.
        for base in ("skills", "shared"):
            for dirpath, _, files in os.walk(os.path.join(ROOT, base)):
                for fn in files:
                    if not fn.endswith((".md", ".py", ".js", ".json")):
                        continue
                    path = os.path.join(dirpath, fn)
                    with self.subTest(path=os.path.relpath(path, ROOT)):
                        with open(path) as f:
                            text = f.read()
                        self.assertNotIn("—", text)


if __name__ == "__main__":
    unittest.main()
