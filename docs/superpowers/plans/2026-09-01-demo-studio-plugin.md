# Demo Studio Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the `demo-studio` monolith into a plugin of six individually invocable skills, single-source the brand and the create-slides, make the guardrails and traces-to mechanically enforced, and make the whole thing run on a stock Mac.

**Architecture:** A plugin root holds a `shared/` layer (brand tokens, guardrails, config validation, pptx tooling) and six skills under `skills/`: a thin router plus five workers, one per pipeline stage. Slides are authored once against a recording kit and replayed through two backends (SVG for previews, pptxgenjs for the deck) so preview fidelity is structural. Discovery becomes a durable artifact with signal ids, which turns the free-text `traces` field into a resolvable reference.

**Tech Stack:** Python 3.9+ (stdlib only, `unittest`), Node 18+ (`node --test`, pptxgenjs for the PPTX backend only), bash for tooling probes.

**Spec:** `docs/superpowers/specs/2026-09-01-demo-studio-plugin-design.md`

## Global Constraints

- **Python floor 3.9**, stdlib only. No `pip install` anywhere in the skill. Every Python file must run under both `/usr/bin/python3` (3.9.6) and `~/.asdf/installs/python/3.12.12/bin/python3`.
- **Node 18+**, built-in test runner. `pptxgenjs` is the only npm dependency, and only the PPTX backend may import it.
- **No em dashes** in any file this plan creates or modifies, including tests, comments, and commit messages. The single exception is a deliberate em-dash literal used as test data or as the `EM_DASH` constant: the guardrail that detects them must contain one. Do not "clean up" those occurrences, or the check silently stops working.
- **No visual change** to generated HTML or PPTX except where a task states one explicitly. Task 1 captures the baseline that proves this.
- **Google-Slides-safe PPTX:** block-arrow autoshapes only (`rightArrow`, `downArrow`, `leftRightArrow`). Never line connectors, never `prstDash`. Solid borders only. Hex without a leading `#`.
- **Slide geometry is fixed:** `LAYOUT_WIDE`, 13.333in x 7.5in. The SVG mirror uses `viewBox="0 0 1333 750"` (inches x 100).
- **Public-safe:** no customer names, participant names, internal hostnames, or credentials in any file.
- **Brand values are data, not literals.** After Task 5, no hex colour literal may appear in generator source.

**Interpreter shorthand used throughout this plan:**

```bash
PY39=/usr/bin/python3
PY312=~/.asdf/installs/python/3.12.12/bin/python3
```

---

## File Structure

Target layout after Task 4. Tasks before that operate on the pre-restructure tree.

```
demo-studio/
  .claude-plugin/plugin.json          plugin manifest
  package.json                        pptxgenjs dep, "test": "node --test"
  shared/
    brand.json                        core tokens + per-surface accents + fonts + act colours
    brand.py                          emits a surface's CSS :root block
    guardrails.py                     text checks (em dash, AI-tells, public-safe) + pptx output checks
    validate_config.py                stdlib schema walker
    traces.py                         resolves traces refs against discovery.json
    pptx_tools.sh                     locate the pptx skill; preflight soffice/pdftoppm
    grounding.md                      provenance discipline, referenced by all five workers
  skills/
    demo-studio/SKILL.md              ROUTER
    demo-discovery/
      SKILL.md
      references/discovery-format.md
      assets/build_discovery.py       discovery.json -> discovery.md
      assets/schema_discovery.py
      assets/examples/discovery.example.json
    build-spec/
      SKILL.md
      references/build-spec.md
      assets/build_spec_template.md
    deck-flow-guide/
      SKILL.md
      references/flow-guide-format.md
      assets/build_flow_guide.py
      assets/schema_flow_guide.py
      assets/examples/flow_guide.example.json
    create-slides/
      SKILL.md
      references/create-slides-pptx.md
      assets/slidekit.js              op recorder + SVG backend + PPTX backend
      assets/lint_slides.js
      assets/build_create_slides.js   the per-engagement template, now using slidekit
    presenter-guide/
      SKILL.md
      references/presenter-guide-format.md
      assets/build_presenter_guide.py
      assets/schema_presenter_guide.py
      assets/examples/presenter_guide.example.json
  tests/
    baseline/                         captured golden output from commit 0e8ba48
    test_brand.py
    test_guardrails.py
    test_validate_config.py
    test_traces.py
    test_generators.py                end-to-end: both guides build on 3.9 and 3.12
    slidekit.test.js
    lint_slides.test.js
```

Responsibility boundaries: `shared/` holds only what two or more skills need. A schema lives beside the generator it validates, because they change together. Tests live in one top-level `tests/` so a single command runs them all.

---

## Task 1: Test harness and captured baseline

Nothing in this repo has tests. This task builds the safety net that every later task's "no visual change" claim depends on.

**Files:**
- Create: `demo-studio/tests/baseline/.gitkeep`
- Create: `demo-studio/tests/capture_baseline.sh`
- Create: `demo-studio/tests/test_generators.py`
- Create: `demo-studio/package.json`

**Interfaces:**
- Consumes: nothing.
- Produces: `tests/baseline/flow-guide.html` and `tests/baseline/presenter-guide.html`, the golden files every later task diffs against. `tests/test_generators.py` exposes `run_generator(script, config, out)` returning `(returncode, stdout, stderr)`.

- [ ] **Step 1: Write the capture script**

```bash
# demo-studio/tests/capture_baseline.sh
# Renders the example configs with the CURRENT generators and stores the output
# as golden files. Run once, before any generator is modified.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
out="$here/baseline"
mkdir -p "$out"

PY="${PY:-python3}"
"$PY" "$root/assets/build_flow_guide.py" \
      "$root/assets/examples/flow_guide.example.json" \
      "$out/flow-guide.html"
"$PY" "$root/assets/build_presenter_guide.py" \
      "$root/assets/examples/presenter_guide.example.json" \
      "$out/presenter-guide.html"
echo "baseline captured in $out"
```

- [ ] **Step 2: Capture the baseline before touching anything**

```bash
cd /Users/dan/code/skills/demo-studio
PY=~/.asdf/installs/python/3.12.12/bin/python3 bash tests/capture_baseline.sh
ls -l tests/baseline/
```

Expected: two HTML files, roughly 15K and 23K.

- [ ] **Step 3: Write the failing test**

```python
# demo-studio/tests/test_generators.py
"""End to end: both generators build, on every supported interpreter, and their
output still matches the captured baseline."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASELINE = os.path.join(HERE, "baseline")

GENERATORS = [
    ("build_flow_guide.py", "flow_guide.example.json", "flow-guide.html"),
    ("build_presenter_guide.py", "presenter_guide.example.json", "presenter-guide.html"),
]


def run_generator(script, config, out):
    """Run a generator. Returns (returncode, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "assets", script),
         os.path.join(ROOT, "assets", "examples", config), out],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


class TestGeneratorsMatchBaseline(unittest.TestCase):
    def test_output_matches_baseline(self):
        for script, config, golden in GENERATORS:
            with self.subTest(script=script):
                with tempfile.TemporaryDirectory() as tmp:
                    out = os.path.join(tmp, golden)
                    rc, _, err = run_generator(script, config, out)
                    self.assertEqual(rc, 0, f"{script} failed: {err}")
                    with open(out) as f:
                        got = f.read()
                    with open(os.path.join(BASELINE, golden)) as f:
                        want = f.read()
                    self.assertEqual(got, want, f"{script} output drifted from baseline")


class TestNoEmDashes(unittest.TestCase):
    def test_generated_output_has_no_em_dashes(self):
        for _, _, golden in GENERATORS:
            with self.subTest(golden=golden):
                with open(os.path.join(BASELINE, golden)) as f:
                    self.assertNotIn("—", f.read())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the tests on both interpreters**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m unittest discover -s tests -v
```

Expected: 3.12 passes both tests. 3.9 **FAILS** `test_output_matches_baseline` with a `SyntaxError` from `build_presenter_guide.py`. That failure is the RED for Task 2, so leave it failing.

- [ ] **Step 5: Add package.json for the JS side**

```json
{
  "name": "demo-studio",
  "private": true,
  "version": "1.0.0",
  "description": "Demo Studio slide tooling",
  "scripts": {
    "test": "node --test"
  },
  "dependencies": {
    "pptxgenjs": "^3.12.0"
  }
}
```

- [ ] **Step 6: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/tests demo-studio/package.json
git commit -m "test: add generator harness and capture pre-change baseline

Golden output captured from the unmodified generators so later tasks can
prove they did not change the rendered result. The 3.9 run fails on
build_presenter_guide.py, which is the known SyntaxError fixed next."
```

---

## Task 2: Fix the Python 3.9 SyntaxError

`build_presenter_guide.py:100` puts an escaped `\"` inside an f-string expression part. That is legal only in 3.12+, so the presenter guide cannot run on stock macOS Python. It is the only such construct in either generator.

**Files:**
- Modify: `demo-studio/assets/build_presenter_guide.py:99-101`
- Modify: `demo-studio/tests/test_generators.py` (add the interpreter-matrix test)

**Interfaces:**
- Consumes: `run_generator` from Task 1.
- Produces: both generators importable and runnable under Python 3.9.

- [ ] **Step 1: Write the failing test**

Append to `demo-studio/tests/test_generators.py`:

```python
class TestInterpreterFloor(unittest.TestCase):
    """Both generators must parse and run on the 3.9 floor, not just 3.12."""

    INTERPRETERS = [p for p in ("/usr/bin/python3",
                                os.path.expanduser("~/.asdf/installs/python/3.12.12/bin/python3"))
                    if os.path.exists(p)]

    def test_generators_compile_on_every_interpreter(self):
        self.assertTrue(self.INTERPRETERS, "no interpreters found to test")
        for interp in self.INTERPRETERS:
            for script, _, _ in GENERATORS:
                with self.subTest(interp=interp, script=script):
                    proc = subprocess.run(
                        [interp, "-m", "py_compile", os.path.join(ROOT, "assets", script)],
                        capture_output=True, text=True)
                    self.assertEqual(proc.returncode, 0,
                                     f"{script} does not compile on {interp}: {proc.stderr}")
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_generators.TestInterpreterFloor -v
```

Expected: FAIL, `build_presenter_guide.py does not compile on /usr/bin/python3: SyntaxError: f-string expression part cannot include a backslash`.

- [ ] **Step 3: Apply the fix**

Current `demo-studio/assets/build_presenter_guide.py:99-101`:

```python
        lanes="".join(
          f'<div class="lane {cls}"><span class="ln"{(" style=\"color:var(--muted)\"" if not cls else "")}>{name}</span><p>{desc}</p></div>'
          for (name,cls,desc) in demo.get("lanes",[]))
```

Replace with (hoist the escaped literal out of the expression part):

```python
        _muted_style = ' style="color:var(--muted)"'
        lanes="".join(
          f'<div class="lane {cls}"><span class="ln"{_muted_style if not cls else ""}>{name}</span><p>{desc}</p></div>'
          for (name,cls,desc) in demo.get("lanes",[]))
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  echo "== $PY"; $PY -m unittest discover -s tests -v
done
```

Expected: all tests pass on both. In particular `test_output_matches_baseline` still passes, proving the fix changed no rendered output.

- [ ] **Step 5: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/assets/build_presenter_guide.py demo-studio/tests/test_generators.py
git commit -m "fix: run the presenter guide generator on Python 3.9

An escaped quote inside an f-string expression part is 3.12-only syntax.
Hoisting it to a variable drops the floor to 3.9 with byte-identical output."
```

---

## Task 3: pptx tooling probe and render preflight

Two portability breaks in one file. The skill references `/mnt/skills/public/pptx/...`, which exists only in the desktop sandbox, and the mandatory visual-QA loop needs `soffice` and `pdftoppm`, neither of which is installed on a stock Mac.

**Files:**
- Create: `demo-studio/shared/pptx_tools.sh`
- Create: `demo-studio/tests/test_pptx_tools.sh`

**Interfaces:**
- Consumes: nothing.
- Produces: three shell functions, sourced by the create-slides skill.
  - `find_pptx_skill` prints the resolved pptx skill directory to stdout, exit 0; on failure prints the probed locations to stderr, exit 1.
  - `check_render_tools` exits 0 if both `soffice` and `pdftoppm` resolve, else 1, printing which are missing.
  - `render_preflight` runs `check_render_tools`; on failure prints the exact brew commands and the `VISUAL QA SKIPPED` banner, exit 1. Never installs anything on its own.

- [ ] **Step 1: Write the failing test**

```bash
# demo-studio/tests/test_pptx_tools.sh
# Plain assertion script. Exit 0 means every case passed.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../shared/pptx_tools.sh
. "$(dirname "$here")/shared/pptx_tools.sh"

fails=0
ok()   { echo "  ok   - $1"; }
bad()  { echo "  FAIL - $1"; fails=$((fails+1)); }

# 1. find_pptx_skill honours an explicit override
tmp="$(mktemp -d)"; mkdir -p "$tmp/pptx"; touch "$tmp/pptx/SKILL.md"
if [ "$(PPTX_SKILL_DIR="$tmp/pptx" find_pptx_skill)" = "$tmp/pptx" ]; then
  ok "find_pptx_skill honours PPTX_SKILL_DIR"
else
  bad "find_pptx_skill ignored PPTX_SKILL_DIR"
fi

# 2. a bogus override is rejected rather than echoed back
if PPTX_SKILL_DIR="$tmp/nope" find_pptx_skill >/dev/null 2>&1; then
  bad "find_pptx_skill accepted a directory with no SKILL.md"
else
  ok "find_pptx_skill rejects a directory with no SKILL.md"
fi

# 3. failure names every probed location, so the error is actionable
out="$(PPTX_SKILL_DIR="$tmp/nope" DEMO_STUDIO_PROBE_ONLY=1 find_pptx_skill 2>&1 || true)"
case "$out" in
  *"/mnt/skills/public/pptx"*) ok "failure message names the sandbox path" ;;
  *) bad "failure message did not name the probed locations" ;;
esac

# 4. check_render_tools reports the specific missing tool
out="$(PATH=/nonexistent check_render_tools 2>&1 || true)"
case "$out" in
  *soffice*pdftoppm*|*pdftoppm*soffice*) ok "check_render_tools names both missing tools" ;;
  *) bad "check_render_tools did not name both missing tools: $out" ;;
esac

# 5. preflight emits the exact banner the skill must surface
out="$(PATH=/nonexistent render_preflight 2>&1 || true)"
case "$out" in
  *"VISUAL QA SKIPPED - SLIDES UNVERIFIED"*) ok "render_preflight emits the unverified banner" ;;
  *) bad "render_preflight banner missing" ;;
esac
case "$out" in
  *"brew install --cask libreoffice"*) ok "render_preflight prints the brew command" ;;
  *) bad "render_preflight did not print the brew command" ;;
esac

rm -rf "$tmp"
[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failure(s)"; exit 1; }
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio && bash tests/test_pptx_tools.sh
```

Expected: FAIL, `shared/pptx_tools.sh: No such file or directory`.

- [ ] **Step 3: Write the implementation**

```bash
# demo-studio/shared/pptx_tools.sh
# Locate the pptx skill and verify the render toolchain. Source this, do not run it.
#
# The skill's visual-QA loop needs the pptx skill's office scripts plus soffice and
# pdftoppm. In the Claude desktop sandbox those live under /mnt; on a developer
# machine they do not. Probe, and fail with something actionable.

# Ordered probe list. First hit that contains SKILL.md wins.
_pptx_candidates() {
  [ -n "${PPTX_SKILL_DIR:-}" ] && printf '%s\n' "$PPTX_SKILL_DIR"
  printf '%s\n' "/mnt/skills/public/pptx"
  printf '%s\n' "$HOME/Library/Application Support/Claude/local-agent-mode-sessions"/*/*/*/skills/pptx
  printf '%s\n' "$HOME/.claude/skills/pptx"
}

find_pptx_skill() {
  local dir
  while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    if [ -f "$dir/SKILL.md" ]; then
      printf '%s\n' "$dir"
      return 0
    fi
  done <<EOF
$(_pptx_candidates)
EOF
  {
    echo "could not locate the pptx skill. Probed:"
    _pptx_candidates | sed 's/^/  /'
    echo "Set PPTX_SKILL_DIR to override."
  } >&2
  return 1
}

check_render_tools() {
  local missing=""
  command -v soffice   >/dev/null 2>&1 || missing="$missing soffice"
  command -v pdftoppm  >/dev/null 2>&1 || missing="$missing pdftoppm"
  if [ -n "$missing" ]; then
    echo "missing render tools:$missing" >&2
    return 1
  fi
  return 0
}

# Gate for the visual-QA loop. Never installs anything: it reports and returns
# non-zero so the caller decides. The banner is the contract with the skill,
# which must surface it to the user rather than reporting the deck as done.
render_preflight() {
  if check_render_tools 2>/dev/null; then
    return 0
  fi
  check_render_tools 2>&1 >/dev/null | sed 's/^/  /' >&2
  cat >&2 <<'BANNER'

  To enable the visual-QA loop:
    brew install --cask libreoffice
    brew install poppler

  ############################################################
  #  VISUAL QA SKIPPED - SLIDES UNVERIFIED                   #
  #  Slides were not rendered or inspected. Do not report    #
  #  this deck as done. Say plainly that visual QA did not   #
  #  run and that layout problems would not have been seen.  #
  ############################################################
BANNER
  return 1
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd /Users/dan/code/skills/demo-studio && bash tests/test_pptx_tools.sh
```

Expected: six `ok` lines then `PASS`.

- [ ] **Step 5: Verify against the real machine state**

```bash
cd /Users/dan/code/skills/demo-studio
. shared/pptx_tools.sh
find_pptx_skill && echo "resolved above"
render_preflight || echo "(preflight correctly reported missing tools, exit $?)"
```

Expected: `find_pptx_skill` resolves to the desktop app's pptx skill directory. `render_preflight` prints the banner and returns 1, because neither tool is installed here.

- [ ] **Step 6: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/shared/pptx_tools.sh demo-studio/tests/test_pptx_tools.sh
git commit -m "feat: probe for the pptx skill and gate the render toolchain

Replaces the hardcoded /mnt path with an ordered probe, and adds a preflight
that reports missing soffice/pdftoppm with the brew commands and a loud
unverified banner instead of failing obscurely."
```

---

## Task 4: Restructure into the plugin layout

Pure move plus the manifest and the SKILL.md split. No behaviour changes, so the Task 1 baseline test is the gate.

**Files:**
- Create: `demo-studio/.claude-plugin/plugin.json`
- Create: `demo-studio/skills/{demo-studio,demo-discovery,build-spec,deck-flow-guide,create-slides,presenter-guide}/SKILL.md`
- Move: every file per the migration table below
- Modify: `demo-studio/tests/test_generators.py` (paths shift)

**Interfaces:**
- Consumes: nothing.
- Produces: the directory layout every later task writes into. Generator paths become `skills/<worker>/assets/<script>.py`.

- [ ] **Step 1: Write the failing test**

```python
# demo-studio/tests/test_layout.py
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

    def test_no_em_dashes_in_any_skill_file(self):
        for dirpath, _, files in os.walk(os.path.join(ROOT, "skills")):
            for fn in files:
                if not fn.endswith((".md", ".py", ".js", ".json")):
                    continue
                path = os.path.join(dirpath, fn)
                with self.subTest(path=os.path.relpath(path, ROOT)):
                    with open(path) as f:
                        self.assertNotIn("—", f.read())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_layout -v
```

Expected: FAIL on every test, nothing exists yet.

- [ ] **Step 3: Perform the moves**

```bash
cd /Users/dan/code/skills/demo-studio
mkdir -p .claude-plugin shared
for s in demo-studio demo-discovery build-spec deck-flow-guide create-slides presenter-guide; do
  mkdir -p "skills/$s/references" "skills/$s/assets"
done
mkdir -p skills/deck-flow-guide/assets/examples skills/presenter-guide/assets/examples

git mv references/grounding.md                shared/grounding.md
git mv references/build-spec.md               skills/build-spec/references/
git mv assets/build_spec_template.md          skills/build-spec/assets/
git mv references/flow-guide-format.md        skills/deck-flow-guide/references/
git mv assets/build_flow_guide.py             skills/deck-flow-guide/assets/
git mv assets/examples/flow_guide.example.json skills/deck-flow-guide/assets/examples/
git mv references/presenter-guide-format.md   skills/presenter-guide/references/
git mv assets/build_presenter_guide.py        skills/presenter-guide/assets/
git mv assets/examples/presenter_guide.example.json skills/presenter-guide/assets/examples/
git mv references/create-slides-pptx.md       skills/create-slides/references/
git mv assets/build_create_slides.js          skills/create-slides/assets/
git mv SKILL.md                               skills/demo-studio/SKILL.md
git rm -q QUICKSTART.md references/pipeline.md   # content redistributed in step 5
rmdir assets/examples assets references 2>/dev/null || true
```

- [ ] **Step 4: Write the manifest**

```json
{
  "name": "demo-studio",
  "description": "Turn a discovery call into a demo build spec, a deck flow guide, the net-new slides, and a presenter guide with a live-demo run of show",
  "version": "1.0.0",
  "author": { "name": "Dan Nemeth" },
  "keywords": ["pre-sales", "demo", "deck", "presenter-guide", "enablement"]
}
```

- [ ] **Step 5: Split SKILL.md into the router plus five stubs**

The router keeps the entry-point map, sequencing and the recommend-then-lock hinge. Each worker gets the deliverable section that belongs to it, lifted verbatim from the old SKILL.md and `references/pipeline.md`. Descriptions are written properly in Task 14; for now each stub carries a minimal valid frontmatter so the layout test passes:

```markdown
---
name: build-spec
description: >-
  Use when the user asks to spec a customer demo, write a build spec, or produce
  something a coding agent can execute end to end to build a demo.
---

# Build Spec

Read `references/build-spec.md`, then fill `assets/build_spec_template.md`.
Apply the disciplines in `../../shared/grounding.md`.
```

Repeat for `demo-discovery`, `deck-flow-guide`, `create-slides`, `presenter-guide`, each pointing at its own references and assets. The router's body keeps the stage list and names workers as `demo-studio:build-spec` and so on, with no `@` links.

- [ ] **Step 6: Update the test harness for the new paths**

In `demo-studio/tests/test_generators.py`, replace the `GENERATORS` table and the path built inside `run_generator`:

```python
GENERATORS = [
    ("deck-flow-guide", "build_flow_guide.py", "flow_guide.example.json", "flow-guide.html"),
    ("presenter-guide", "build_presenter_guide.py", "presenter_guide.example.json", "presenter-guide.html"),
]


def run_generator(skill, script, config, out):
    """Run a generator. Returns (returncode, stdout, stderr)."""
    base = os.path.join(ROOT, "skills", skill, "assets")
    proc = subprocess.run(
        [sys.executable, os.path.join(base, script),
         os.path.join(base, "examples", config), out],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr
```

Update the three call sites to unpack four-tuples and pass `skill`.

- [ ] **Step 6b: Update capture_baseline.sh for the new paths**

Task 5 re-runs this script, so it must follow the move. Replace the two
generator invocations:

```bash
"$PY" "$root/skills/deck-flow-guide/assets/build_flow_guide.py" \
      "$root/skills/deck-flow-guide/assets/examples/flow_guide.example.json" \
      "$out/flow-guide.html"
"$PY" "$root/skills/presenter-guide/assets/build_presenter_guide.py" \
      "$root/skills/presenter-guide/assets/examples/presenter_guide.example.json" \
      "$out/presenter-guide.html"
```

Verify it still reproduces the golden files byte for byte:

```bash
cd /Users/dan/code/skills/demo-studio
cp tests/baseline/flow-guide.html /tmp/golden-flow.html
PY=~/.asdf/installs/python/3.12.12/bin/python3 bash tests/capture_baseline.sh
diff /tmp/golden-flow.html tests/baseline/flow-guide.html && echo "baseline reproduces exactly"
```

- [ ] **Step 7: Run every test**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  echo "== $PY"; $PY -m unittest discover -s tests -v
done
bash tests/test_pptx_tools.sh
```

Expected: all pass. `test_output_matches_baseline` passing here is the proof that the restructure changed no rendered output.

- [ ] **Step 8: Commit**

```bash
cd /Users/dan/code/skills
git add -A demo-studio
git commit -m "refactor: restructure demo-studio into a plugin of six skills

Router plus five workers, shared/ for what more than one skill needs.
Pure move: baseline output is unchanged, proven by the golden test."
```

---

## Task 5: Single-source the brand

Today the palette is hardcoded three times. The two guides have genuinely divergent accent values, so `brand.json` models a shared core plus per-surface overrides, reproducing each surface's current `:root` byte for byte.

**Files:**
- Create: `demo-studio/shared/brand.json`
- Create: `demo-studio/shared/brand.py`
- Create: `demo-studio/tests/test_brand.py`
- Modify: `demo-studio/skills/deck-flow-guide/assets/build_flow_guide.py` (the `:root` block and 3 stray hexes)
- Modify: `demo-studio/skills/presenter-guide/assets/build_presenter_guide.py` (the `:root` block and 10 stray hexes)

**Interfaces:**
- Consumes: nothing.
- Produces: `shared/brand.py` exposing
  - `load()` returning the parsed brand dict,
  - `tokens(surface)` returning an ordered `dict[str, str]` of CSS variable name to hex for that surface,
  - `root_block(surface, indent="  ", sep="\n")` returning the full `:root{...}` CSS text,
  - `FONTS` as `dict` with keys `heading`, `body`, `mono`,
  - `acts()` returning the act-name to hex map.
  Surfaces are the literals `"flow_guide"`, `"presenter_guide"`, `"pptx"`.

- [ ] **Step 1: Write the failing test**

```python
# demo-studio/tests/test_brand.py
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_brand -v
```

Expected: FAIL, `ModuleNotFoundError: No module named 'brand'`.

- [ ] **Step 3: Write brand.json**

```json
{
  "_note": "Single source for colour and type. 'core' is shared by every surface; a surface may override or extend it. flow_guide and presenter_guide carry different accent values today, which is preserved deliberately: unifying them would restyle a shipped guide.",
  "core": {
    "indigo": "#4C2889",
    "indigo-ink": "#2A1650",
    "indigo-tint": "#EFEAF6",
    "ink": "#1C1526",
    "paper": "#F6F4FA",
    "card": "#FFFFFF",
    "muted": "#6A6478",
    "line": "#E4E0EC"
  },
  "surfaces": {
    "flow_guide": {
      "amber": "#E0A100",
      "green": "#3B8C6E",
      "green-tint": "#E8F2ED",
      "green-ink": "#245A44",
      "coral": "#E2664A",
      "coral-tint": "#FBEDE8",
      "coral-ink": "#B24326",
      "drill-line": "#E7B8A8",
      "drill-hover": "#8F351D",
      "hbox-border": "#D8CDE9"
    },
    "presenter_guide": {
      "faint": "#8B84A3",
      "amber": "#B07A00",
      "green": "#2E7D5B",
      "green-tint": "#E8F2ED",
      "green-border": "#CDE7DB",
      "green-ink": "#245A44",
      "coral": "#C0503A",
      "coral-tint": "#FBEDE8",
      "coral-border": "#F0D8CE",
      "coral-ink": "#B24326",
      "term-bg": "#241C33",
      "term-fg": "#F4F1FB",
      "term-accent": "#F5A38A",
      "on-dark": "#C9B8F0",
      "on-dark-body": "#E7DEFA",
      "on-dark-pre": "#E7E2F5"
    },
    "pptx": {
      "bg": "#17131F",
      "panel": "#241C33",
      "panel2": "#1E1830",
      "wf": "#2C2247",
      "border": "#3A3350",
      "indigo": "#8E6BE6",
      "indigo-backbone": "#6E4FC0",
      "coral": "#F0805E",
      "coral-fill": "#2A1D1A",
      "green": "#5FBE97",
      "amber": "#E9B23A",
      "txt": "#F4F1FB",
      "mut": "#B4AECA",
      "faint": "#8B84A3"
    }
  },
  "fonts": {
    "heading": "Fraunces",
    "body": "IBM Plex Sans",
    "mono": "JetBrains Mono"
  },
  "acts": {
    "Open": "#1C1526",
    "Frame": "#B07A00",
    "Model": "#4C2889",
    "Prime": "#2E7D5B",
    "Prove": "#C0503A",
    "Handoff": "#6E4FC0",
    "Demo": "#1C1526"
  }
}
```

- [ ] **Step 4: Write brand.py**

```python
# demo-studio/shared/brand.py
"""Single source for the brand system.

Colour and type live in brand.json. Generators ask for a surface's tokens and
render them into a CSS :root block, so changing one hex changes every artifact.
Stdlib only, Python 3.9 compatible.
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_HERE, "brand.json")

_cache = None


def load():
    """Parse brand.json once and memoise it."""
    global _cache
    if _cache is None:
        with open(_PATH) as f:
            _cache = json.load(f)
    return _cache


def tokens(surface):
    """Ordered token map for a surface: core first, then that surface's own.

    Raises KeyError for an unknown surface, so a typo fails loudly rather than
    silently rendering an unstyled page.
    """
    data = load()
    surfaces = data["surfaces"]
    if surface not in surfaces:
        raise KeyError(
            "unknown surface %r, expected one of %s"
            % (surface, ", ".join(sorted(surfaces)))
        )
    merged = dict(data["core"])
    merged.update(surfaces[surface])
    return merged


def root_block(surface, indent="  ", sep="\n"):
    """The CSS :root{...} declaration for a surface."""
    lines = [
        "%s--%s:%s;" % (indent, name, value)
        for name, value in tokens(surface).items()
    ]
    return ":root{" + sep + sep.join(lines) + sep + "}"


def acts():
    """Act name to hex, used for presenter-guide nav colouring."""
    return dict(load()["acts"])


FONTS = load()["fonts"]
```

- [ ] **Step 5: Wire the flow-guide generator**

In `skills/deck-flow-guide/assets/build_flow_guide.py`, add the import near the top:

```python
import html, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "shared"))
import brand
```

Replace the literal `:root{...}` at the head of `CSS` with a placeholder, and substitute at build time. Change the `CSS = r''':root{ ... }` opening so the block begins after the brace, then where the page is assembled prepend `brand.root_block("flow_guide")`:

```python
CSS = brand.root_block("flow_guide") + r'''
  *{box-sizing:border-box;}
  ...unchanged from here...
'''
```

Then replace the three stray hexes with the new tokens:

| Line | Was | Becomes |
|---|---|---|
| `details.drill` border-top | `#E7B8A8` | `var(--drill-line)` |
| `details.drill summary:hover` | `#8f351d` | `var(--drill-hover)` |
| `.hbox` border | `#D8CDE9` | `var(--hbox-border)` |

- [ ] **Step 6: Wire the presenter-guide generator**

Same import block, same `CSS = brand.root_block("presenter_guide") + r'''...'''` change, then replace the ten stray hexes:

| Was | Becomes |
|---|---|
| `#F0D8CE` (`.qcard` border) | `var(--coral-border)` |
| `#C9B8F0` (`.demobanner .eyebrow`, `.switchblock .sw-t`) | `var(--on-dark)` |
| `#E7DEFA` (`.demobanner p`) | `var(--on-dark-body)` |
| `#B24326` (`.lane.work .ln`) | `var(--coral-ink)` |
| `#CDE7DB` (`.smoke` border) | `var(--green-border)` |
| `#245A44` (`.smoke` colour) | `var(--green-ink)` |
| `#241C33` (`.term-action`, `.switchblock`) | `var(--term-bg)` |
| `#F4F1FB` (`.term-action`) | `var(--term-fg)` |
| `#F5A38A` (`.term-action b`) | `var(--term-accent)` |
| `#E7E2F5` (`.switchblock pre`) | `var(--on-dark-pre)` |

- [ ] **Step 7: Re-capture the baseline, then diff it deliberately**

The `:root` block is now generated, so whitespace and token order may differ from the literal even though every rendered colour is identical. Byte-identity is the wrong bar here, per spec V2. Inspect the diff and confirm every line is a `:root` reformatting or a hex-to-`var()` swap, then re-baseline:

```bash
cd /Users/dan/code/skills/demo-studio
PY=~/.asdf/installs/python/3.12.12/bin/python3
$PY skills/deck-flow-guide/assets/build_flow_guide.py \
    skills/deck-flow-guide/assets/examples/flow_guide.example.json /tmp/new-flow.html
diff <(sed -n '/<style>/,/<\/style>/p' tests/baseline/flow-guide.html) \
     <(sed -n '/<style>/,/<\/style>/p' /tmp/new-flow.html)
# Confirm: only :root reformatting and var() substitutions. Then:
PY=$PY bash tests/capture_baseline.sh
```

Do the same for the presenter guide. **Open both regenerated files in a browser and compare against the old ones before re-baselining.** A `var()` pointing at a token that does not exist renders as no colour at all, which no text diff will catch.

- [ ] **Step 8: Run every test**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  echo "== $PY"; $PY -m unittest discover -s tests -v
done
```

Expected: all pass, including `test_generators_contain_no_hex_literals`.

- [ ] **Step 9: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/shared/brand.json demo-studio/shared/brand.py \
        demo-studio/tests/test_brand.py demo-studio/tests/baseline \
        demo-studio/skills/deck-flow-guide/assets/build_flow_guide.py \
        demo-studio/skills/presenter-guide/assets/build_presenter_guide.py
git commit -m "refactor: single-source the brand system in brand.json

Core tokens are shared; flow_guide and presenter_guide keep their divergent
accent values so neither guide is restyled. No hex literal remains in any
generator."
```

---

## Task 6: Guardrails, text checks

The disciplines the skill states as prose become a module that fails a build.

**Files:**
- Create: `demo-studio/shared/guardrails.py`
- Create: `demo-studio/tests/test_guardrails.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `shared/guardrails.py` exposing
  - `Violation`, a `namedtuple` with fields `check`, `field`, `detail`,
  - `EM_DASH` (the literal `"—"`) and `AI_TELLS` (a tuple of lowercase words),
  - `check_text(value, field, allowlist=()) -> list[Violation]`,
  - `check_tree(obj, allowlist=(), banned=()) -> list[Violation]` walking dicts, lists and strings, building dotted paths like `acts[0].cards[1].why`,
  - `report(violations) -> str` formatting one violation per line,
  - `enforce(violations)` raising `GuardrailError` when the list is non-empty,
  - `GuardrailError(Exception)`.

- [ ] **Step 1: Write the failing test**

```python
# demo-studio/tests/test_guardrails.py
"""Mechanical enforcement of the rules the skill previously only documented."""
import os
import sys
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_guardrails -v
```

Expected: FAIL, `ModuleNotFoundError: No module named 'guardrails'`.

- [ ] **Step 3: Write the implementation**

```python
# demo-studio/shared/guardrails.py
"""Mechanical enforcement of the Demo Studio guardrails.

The skill documents these as disciplines. Documented rules get forgotten under
pressure, so they are checked here and hard-fail the build. Stdlib only,
Python 3.9 compatible.
"""
import re
from collections import namedtuple

Violation = namedtuple("Violation", "check field detail")

EM_DASH = "—"

# Filler that reads as machine-written. Engineer-to-engineer register is terse.
AI_TELLS = (
    "seamless", "robust", "leverage", "genuinely",
    "delve", "honestly", "actually",
)


class GuardrailError(Exception):
    """Raised when a build would ship a guardrail violation."""


def _word_re(word):
    return re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)


_TELL_RES = tuple((w, _word_re(w)) for w in AI_TELLS)


def check_text(value, field, allowlist=(), banned=()):
    """Check one string. Returns a list of Violation, empty when clean."""
    if not isinstance(value, str):
        return []
    out = []
    if EM_DASH in value:
        out.append(Violation("em-dash", field, "use a comma or restructure"))
    permitted = {w.lower() for w in allowlist}
    for word, pattern in _TELL_RES:
        if word in permitted:
            continue
        if pattern.search(value):
            out.append(Violation("ai-tell", field, word))
    for term in banned:
        if _word_re(term).search(value):
            out.append(Violation("public-safe", field, term))
    return out


def check_tree(obj, allowlist=(), banned=(), _path=""):
    """Walk a config tree, checking every string value.

    Paths read like acts[0].cards[1].why so a failure points at the exact field
    the author has to edit.
    """
    out = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = key if not _path else "%s.%s" % (_path, key)
            out.extend(check_tree(value, allowlist, banned, child))
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            out.extend(check_tree(value, allowlist, banned, "%s[%d]" % (_path, i)))
    elif isinstance(obj, str):
        out.extend(check_text(obj, _path or "<root>", allowlist, banned))
    return out


def report(violations):
    """One violation per line, ordered as found."""
    return "\n".join(
        "  %-12s %-40s %s" % (v.check, v.field, v.detail) for v in violations
    )


def enforce(violations):
    """Raise if anything was found. Call this before writing any output file."""
    if violations:
        raise GuardrailError(
            "%d guardrail violation(s):\n%s" % (len(violations), report(violations))
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  $PY -m unittest tests.test_guardrails -v
done
```

Expected: all pass on both interpreters.

- [ ] **Step 5: Wire it into both generators**

In each generator's `main`, after the config is loaded and before anything is written:

```python
import guardrails
...
    allowlist = cfg.get("allow_words", ())
    banned = cfg.get("banned_terms", ())
    guardrails.enforce(guardrails.check_tree(cfg, allowlist=allowlist, banned=banned))
```

`allow_words` is the documented escape for a legitimate technical use of a listed word. It is an explicit per-term allowlist, never a flag that disables the check.

- [ ] **Step 6: Verify the wiring with a seeded violation**

```bash
cd /Users/dan/code/skills/demo-studio
PY=~/.asdf/installs/python/3.12.12/bin/python3
$PY - <<'EOF'
import json, pathlib
p = pathlib.Path("skills/deck-flow-guide/assets/examples/flow_guide.example.json")
cfg = json.loads(p.read_text())
cfg["acts"][0]["cards"][0]["why"] = "a seamless — story"
pathlib.Path("/tmp/bad_flow.json").write_text(json.dumps(cfg))
EOF
$PY skills/deck-flow-guide/assets/build_flow_guide.py /tmp/bad_flow.json /tmp/out.html; echo "exit=$?"
```

Expected: non-zero exit, and the error names both `em-dash` and `ai-tell` at `acts[0].cards[0].why`. Confirm `/tmp/out.html` was not written.

- [ ] **Step 7: Run the full suite and commit**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest discover -s tests -v
cd /Users/dan/code/skills
git add demo-studio/shared/guardrails.py demo-studio/tests/test_guardrails.py \
        demo-studio/skills/deck-flow-guide/assets/build_flow_guide.py \
        demo-studio/skills/presenter-guide/assets/build_presenter_guide.py
git commit -m "feat: enforce the text guardrails mechanically

Em dashes, AI-tell filler and banned identifiers now fail the build with the
offending field named, instead of relying on the author remembering the rule."
```

---

## Task 7: Guardrails, PPTX output checks

Google Slides silently drops line connectors and dashed lines on import, so a deck can look fine locally and arrive broken. This check reads the generated file rather than trusting the builder.

**Files:**
- Modify: `demo-studio/shared/guardrails.py` (add the pptx section)
- Modify: `demo-studio/tests/test_guardrails.py` (add the pptx test class)
- Create: `demo-studio/tests/fixtures/make_bad_pptx.py`

**Interfaces:**
- Consumes: `Violation`, `GuardrailError` from Task 6.
- Produces: `check_pptx(path) -> list[Violation]`, reading the `.pptx` as a zip and scanning every `ppt/slides/slide*.xml` for banned drawing constructs.

- [ ] **Step 1: Write the fixture builder**

`pptxgenjs` cannot emit a connector, so the fixture writes the minimal OOXML by hand.

```python
# demo-studio/tests/fixtures/make_bad_pptx.py
"""Build a minimal .pptx containing the constructs Google Slides drops, so the
guardrail has something real to catch."""
import sys
import zipfile

SLIDE_WITH_CONNECTOR = """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:cxnSp><p:nvCxnSpPr/><p:spPr><a:prstGeom prst="straightConnector1"/></p:spPr></p:cxnSp>
    <p:sp><p:spPr><a:ln><a:prstDash val="dash"/></a:ln></p:spPr></p:sp>
  </p:spTree></p:cSld>
</p:sld>
"""

CLEAN_SLIDE = """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:sp><p:spPr><a:prstGeom prst="rightArrow"/><a:ln><a:solidFill/></a:ln></p:spPr></p:sp>
  </p:spTree></p:cSld>
</p:sld>
"""


def write(path, xml):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/slides/slide1.xml", xml)


if __name__ == "__main__":
    kind, path = sys.argv[1], sys.argv[2]
    write(path, SLIDE_WITH_CONNECTOR if kind == "bad" else CLEAN_SLIDE)
```

- [ ] **Step 2: Write the failing test**

Append to `demo-studio/tests/test_guardrails.py`:

```python
import subprocess
import tempfile


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
```

- [ ] **Step 3: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_guardrails.TestPptxChecks -v
```

Expected: FAIL, `module 'guardrails' has no attribute 'check_pptx'`.

- [ ] **Step 4: Write the implementation**

Append to `demo-studio/shared/guardrails.py`:

```python
import zipfile

# Constructs Google Slides silently drops on import. A deck can look correct in
# PowerPoint and arrive in Slides with its arrows missing, so check the file.
_PPTX_BANNED = (
    ("pptx-connector", re.compile(r"<p:cxnSp[ >]"),
     "line connector, use a block arrow autoshape"),
    ("pptx-connector", re.compile(r'prst="(straight|bent|curved)Connector'),
     "connector geometry, use a block arrow autoshape"),
    ("pptx-dash", re.compile(r"<a:prstDash[ >]"),
     "dashed line, use a solid border"),
)


def check_pptx(path):
    """Scan a generated .pptx for constructs that do not survive Google Slides."""
    out = []
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist()
                       if re.match(r"ppt/slides/slide\d+\.xml$", n))
        for name in names:
            slide = re.sub(r".*/(slide\d+)\.xml$", r"\1", name)
            xml = z.read(name).decode("utf-8", "replace")
            for check, pattern, detail in _PPTX_BANNED:
                if pattern.search(xml):
                    out.append(Violation(check, slide, detail))
    return out
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  $PY -m unittest tests.test_guardrails -v
done
```

Expected: all pass on both.

- [ ] **Step 6: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/shared/guardrails.py demo-studio/tests/test_guardrails.py \
        demo-studio/tests/fixtures
git commit -m "feat: check generated PPTX for Google-Slides-unsafe constructs

Reads the .pptx as a zip and flags connectors and dashed lines per slide.
Checks the artifact rather than trusting the builder."
```

---

## Task 8: Config validation

A typo in a hand-edited config currently produces a traceback or a silently malformed page. Validation must name the offending path.

**Files:**
- Create: `demo-studio/shared/validate_config.py`
- Create: `demo-studio/skills/deck-flow-guide/assets/schema_flow_guide.py`
- Create: `demo-studio/skills/presenter-guide/assets/schema_presenter_guide.py`
- Create: `demo-studio/tests/test_validate_config.py`
- Modify: both generators (call validation before build)

**Interfaces:**
- Consumes: nothing.
- Produces: `shared/validate_config.py` exposing
  - `ConfigError(Exception)`,
  - `validate(config, schema, name="config") -> list[str]` returning human-readable error strings, empty when valid,
  - `enforce(config, schema, name="config")` raising `ConfigError` with every error joined by newlines.
  Schema dialect, deliberately tiny: a dict with keys `type` (`"object"`, `"array"`, `"string"`, `"number"`, `"boolean"`, or a tuple of those), `required` (list of keys, objects only), `properties` (dict, objects only), `items` (schema, arrays only), `enum` (list of permitted values), `minLength` (strings). Unknown keys in an object are allowed, so configs can carry extra fields.

- [ ] **Step 1: Write the failing test**

```python
# demo-studio/tests/test_validate_config.py
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_validate_config -v
```

Expected: FAIL, `ModuleNotFoundError: No module named 'validate_config'`.

- [ ] **Step 3: Write the validator**

```python
# demo-studio/shared/validate_config.py
"""A very small schema walker.

Deliberately not jsonschema: the skill must run with no pip install. This covers
the shapes the Demo Studio configs actually use and reports every problem with a
dotted path, so an author can go straight to the field.
"""

class ConfigError(Exception):
    """Raised when a config does not satisfy its schema."""


_TYPE_NAMES = {
    "object": dict,
    "array": (list, tuple),
    "string": str,
    "number": (int, float),
    "boolean": bool,
}


def _type_name(value):
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if value is None:
        return "null"
    return type(value).__name__


def _matches(value, expected):
    names = (expected,) if isinstance(expected, str) else tuple(expected)
    for name in names:
        wanted = _TYPE_NAMES.get(name)
        if wanted is None:
            continue
        # bool is a subclass of int; keep them distinct
        if name == "number" and isinstance(value, bool):
            continue
        if isinstance(value, wanted):
            return True
    return False


def _walk(value, schema, path, name, errors):
    def fail(message):
        where = path or "<root>"
        errors.append("%s: %s: %s" % (name, where, message))

    expected = schema.get("type")
    if expected is not None and not _matches(value, expected):
        want = expected if isinstance(expected, str) else " or ".join(expected)
        fail("expected %s, got %s" % (want, _type_name(value)))
        return  # structure is wrong, deeper checks would be noise

    if "enum" in schema and value not in schema["enum"]:
        fail("expected one of %s, got %r"
             % (", ".join(repr(v) for v in schema["enum"]), value))

    if isinstance(value, str) and "minLength" in schema:
        if len(value) < schema["minLength"]:
            fail("must be at least %d character(s)" % schema["minLength"])

    if isinstance(value, dict):
        for key in schema.get("required", ()):
            if key not in value:
                child = key if not path else "%s.%s" % (path, key)
                errors.append("%s: %s: required field missing" % (name, child))
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                child = key if not path else "%s.%s" % (path, key)
                _walk(value[key], sub, child, name, errors)

    elif isinstance(value, (list, tuple)) and "items" in schema:
        for i, item in enumerate(value):
            _walk(item, schema["items"], "%s[%d]" % (path, i), name, errors)


def validate(config, schema, name="config"):
    """Return a list of human-readable errors, empty when the config is valid."""
    errors = []
    _walk(config, schema, "", name, errors)
    return errors


def enforce(config, schema, name="config"):
    """Raise ConfigError listing every problem. Call before building anything."""
    errors = validate(config, schema, name)
    if errors:
        raise ConfigError("%d config error(s):\n%s" % (len(errors), "\n".join(errors)))
```

- [ ] **Step 4: Write the flow-guide schema**

Derived from `references/flow-guide-format.md` and the shipped example.

```python
# demo-studio/skills/deck-flow-guide/assets/schema_flow_guide.py
"""Schema for a flow-guide config. See references/flow-guide-format.md."""

_PAIR = {"type": "array", "items": {"type": "string"}}

_PREVIEW = {
    "type": "object",
    "required": ["eyebrow", "title", "body"],
    "properties": {
        "eyebrow": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "sub": {"type": "string"},
        "body": {"type": "string", "minLength": 1},
    },
}

_CARD = {
    "type": "object",
    "required": ["type", "seq", "title", "why", "traces"],
    "properties": {
        "type": {"type": "string", "enum": ["deck", "create"]},
        # seq and act.no are STRINGS in the shipped example ("01", "02"), not numbers.
        # Accept both so the example validates and a numeric config still works.
        "seq": {"type": ["number", "string"]},
        "title": {"type": "string", "minLength": 1},
        "why": {"type": "string", "minLength": 1},
        "traces": {"type": "string"},
        "src_label": {"type": "string"},
        "deckid_label": {"type": "string"},
        "deckid_quote": {"type": "string"},
        "deckid_pg": {"type": "string"},
        "preview": _PREVIEW,
    },
}

_ACT = {
    "type": "object",
    "required": ["no", "title", "cards"],
    "properties": {
        "no": {"type": ["number", "string"]},
        "title": {"type": "string", "minLength": 1},
        "purpose": {"type": "string"},
        "time": {"type": "string"},
        "cards": {"type": "array", "items": _CARD},
    },
}

SCHEMA = {
    "type": "object",
    "required": ["tab_title", "title", "acts"],
    "properties": {
        "tab_title": {"type": "string", "minLength": 1},
        "eyebrow": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "subtitle": {"type": "string"},
        "chips": {"type": "array", "items": _PAIR},
        "legend": {"type": "object"},
        "acts": {"type": "array", "items": _ACT},
        "footer": {"type": "object"},
        "discovery": {"type": "string"},
        "allow_words": {"type": "array", "items": {"type": "string"}},
        "banned_terms": {"type": "array", "items": {"type": "string"}},
    },
}
```

A `deck` card needs `deckid_quote` and a `create` card needs `preview`, which this dialect cannot express conditionally. Task 11's lint is the wrong home for it, so add the pair check directly to the generator right after `enforce`:

```python
for ai, act in enumerate(cfg["acts"]):
    for ci, card in enumerate(act.get("cards", [])):
        where = "acts[%d].cards[%d]" % (ai, ci)
        if card["type"] == "deck" and not card.get("deckid_quote"):
            raise validate_config.ConfigError(
                "%s: a deck card needs deckid_quote, the verbatim slide headline"
                % where)
        if card["type"] == "create" and not card.get("preview"):
            raise validate_config.ConfigError(
                "%s: a create card needs a preview block" % where)
```

- [ ] **Step 5: Write the presenter-guide schema**

```python
# demo-studio/skills/presenter-guide/assets/schema_presenter_guide.py
"""Schema for a presenter-guide config. See references/presenter-guide-format.md."""

_STRINGS = {"type": "array", "items": {"type": "string"}}

_SLIDE = {
    "type": "object",
    "required": ["num", "act", "short", "title"],
    "properties": {
        "num": {"type": ["number", "string"]},
        "act": {"type": "string", "minLength": 1},
        "short": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "onscreen": {"type": "string"},
        "points": _STRINGS,
        "say": _STRINGS,
        "ask": _STRINGS,
    },
}

_BEAT = {
    "type": "object",
    "required": ["id", "title", "rows"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "badge": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "tag": {"type": "string"},
        "accent": {"type": "string", "enum": ["indigo", "coral", "green", "amber"]},
        "term": {"type": "string"},
        "rows": {"type": "array"},
        "note": {"type": "string"},
        "nav": {"type": "string"},
    },
}

_DEMO = {
    "type": "object",
    "properties": {
        "nav_divider": {"type": "string"},
        "banner": {"type": "object"},
        "talk_track": {"type": "string"},
        "lanes": {"type": "array"},
        "termmap": {"type": "array"},
        "smoke": {"type": "string"},
        "beats": {"type": "array", "items": _BEAT},
        "scenarios": {"type": "array"},
        "switches": {"type": "array"},
        "switch_note": {"type": "string"},
        "troubleshooting": {"type": "array"},
    },
}

SCHEMA = {
    "type": "object",
    "required": ["tab_title", "title", "acts", "slides"],
    "properties": {
        "tab_title": {"type": "string", "minLength": 1},
        "nav_title": {"type": "string"},
        "nav_sub": {"type": "string"},
        "eyebrow": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "subtitle": {"type": "string"},
        "chips": {"type": "array"},
        "legend": {"type": "array"},
        "acts": {"type": "object"},
        "slides": {"type": "array", "items": _SLIDE},
        "demo": _DEMO,
        "discovery": {"type": "string"},
        "allow_words": _STRINGS,
        "banned_terms": _STRINGS,
    },
}
```

Every slide's `act` must be a key in `acts`; the dialect cannot express that either, so add it after `enforce`:

```python
for i, slide in enumerate(cfg["slides"]):
    if slide["act"] not in cfg["acts"]:
        raise validate_config.ConfigError(
            "slides[%d].act: %r is not a key in acts (have: %s)"
            % (i, slide["act"], ", ".join(sorted(cfg["acts"]))))
```

- [ ] **Step 6: Wire validation into both generators**

In each generator's `main`, immediately after loading the config and before the guardrail call:

```python
import validate_config
...
    validate_config.enforce(cfg, SCHEMA, name=os.path.basename(cfg_path))
    # then the deck/create pair check or the act-key check shown above
    # then guardrails.enforce(...)
```

Wrap the top-level call so an author sees the message rather than a traceback:

```python
if __name__ == "__main__":
    try:
        main()
    except (validate_config.ConfigError, guardrails.GuardrailError) as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)
```

- [ ] **Step 7: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  $PY -m unittest discover -s tests -v
done
```

Expected: all pass, including the two `TestRealSchemas` cases proving the shipped examples satisfy their own schemas.

- [ ] **Step 8: Verify the error surface by hand**

```bash
cd /Users/dan/code/skills/demo-studio
echo '{"tab_title":"x","acts":[{"no":1,"title":"t","cards":[{"type":"slide","seq":1}]}]}' > /tmp/bad.json
~/.asdf/installs/python/3.12.12/bin/python3 \
  skills/deck-flow-guide/assets/build_flow_guide.py /tmp/bad.json /tmp/o.html; echo "exit=$?"
```

Expected: exit 1, no traceback, and errors naming `<root>: title: required field missing` plus `acts[0].cards[0].type: expected one of 'deck', 'create'`.

- [ ] **Step 9: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/shared/validate_config.py demo-studio/tests/test_validate_config.py \
        demo-studio/skills/deck-flow-guide/assets demo-studio/skills/presenter-guide/assets
git commit -m "feat: validate guide configs with path-naming errors

Stdlib schema walker, no pip dependency. Reports every problem at once and
names the field, replacing tracebacks and silently malformed pages."
```

---

## Task 9: slidekit, op recorder and SVG backend

A create-slide is authored once against a recording kit. This task builds the kit and the SVG backend; Task 10 adds the PPTX backend and proves they agree.

**Files:**
- Create: `demo-studio/skills/create-slides/assets/slidekit.js`
- Create: `demo-studio/tests/slidekit.test.js`

**Interfaces:**
- Consumes: nothing.
- Produces: `slidekit.js` (CommonJS) exporting
  - `LAYOUT` = `{ w: 13.333, h: 7.5 }` and `SCALE` = `100`,
  - `recordSlide(meta, build) -> {eyebrow, title, sub, ops}` where `meta` is `{eyebrow, title, sub}` and `build` receives a recorder `k` with `k.box(x,y,w,h,opts)`, `k.frame(x,y,w,h,color)`, `k.arrowR(x,y,w,h,color)`, `k.arrowD(x,y,w,h,color)`, `k.label(x,y,w,text,color,size,align)`,
  - `bboxes(slide) -> [{op, x, y, w, h}]` in inches, the shared geometric truth,
  - `renderSvg(slide) -> string`, a complete `<svg viewBox="0 0 1333 750">`,
  - `LABEL_H` = `0.28`, the fixed label height inherited from the original helper.

- [ ] **Step 1: Write the failing test**

```js
// demo-studio/tests/slidekit.test.js
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

const kit = require(path.join(__dirname, '..', 'skills', 'create-slides', 'assets', 'slidekit.js'));

const IND = '8E6BE6';

function sample() {
  return kit.recordSlide(
    { eyebrow: 'SETUP FLOW 03', title: 'Two lanes', sub: 'One dies' },
    (k) => {
      k.box(0.6, 2.2, 3.4, 1.2, { rt: 'Platform' });
      k.arrowR(4.2, 2.6, 0.5, 0.4, IND);
      k.frame(5.0, 2.2, 3.4, 1.2, IND);
      k.label(0.6, 3.5, 3.4, 'SURVIVES A CRASH', IND, 9, 'center');
    });
}

test('LAYOUT is the real slide geometry', () => {
  assert.strictEqual(kit.LAYOUT.w, 13.333);
  assert.strictEqual(kit.LAYOUT.h, 7.5);
  assert.strictEqual(kit.SCALE, 100);
});

test('recordSlide captures meta and every op in order', () => {
  const s = sample();
  assert.strictEqual(s.title, 'Two lanes');
  assert.strictEqual(s.sub, 'One dies');
  assert.deepStrictEqual(s.ops.map((o) => o.op), ['box', 'arrowR', 'frame', 'label']);
});

test('bboxes are reported in inches', () => {
  const b = kit.bboxes(sample());
  assert.deepStrictEqual(b[0], { op: 'box', x: 0.6, y: 2.2, w: 3.4, h: 1.2 });
  assert.deepStrictEqual(b[1], { op: 'arrowR', x: 4.2, y: 2.6, w: 0.5, h: 0.4 });
});

test('a label gets the fixed inherited height', () => {
  const b = kit.bboxes(sample());
  assert.strictEqual(b[3].h, kit.LABEL_H);
  assert.strictEqual(kit.LABEL_H, 0.28);
});

test('renderSvg uses a viewBox matching the slide aspect ratio', () => {
  const svg = kit.renderSvg(sample());
  assert.match(svg, /viewBox="0 0 1333 750"/);
  // 1333/750 is 1.777, the real 16:9 slide. The old previews used 760x330,
  // which is 2.30:1, so a preview was a differently shaped drawing.
  assert.doesNotMatch(svg, /760 330/);
});

test('renderSvg geometry is bboxes scaled by SCALE', () => {
  const s = sample();
  const svg = kit.renderSvg(s);
  const b = kit.bboxes(s)[0];
  // Use the kit's own converter, not raw multiplication: b.y * 100 is
  // 220.00000000000003 for y=2.2, which is not what lands in the SVG.
  const u = kit._internal.u;
  assert.match(svg, new RegExp(`x="${u(b.x)}"`));
  assert.match(svg, new RegExp(`y="${u(b.y)}"`));
  assert.match(svg, new RegExp(`width="${u(b.w)}"`));
  assert.match(svg, new RegExp(`height="${u(b.h)}"`));
});

test('SVG coordinates carry no floating point noise', () => {
  const svg = kit.renderSvg(sample());
  const coords = [...svg.matchAll(/(?:x|y|width|height)="([-\d.]+)"/g)].map((m) => m[1]);
  assert.ok(coords.length > 0, 'no coordinates found to check');
  for (const c of coords) {
    assert.ok(!/\d{6,}/.test(c), `coordinate ${c} carries float noise`);
  }
});

test('renderSvg escapes text so a config cannot inject markup', () => {
  const s = kit.recordSlide({ eyebrow: 'E', title: 'T', sub: '' },
    (k) => k.label(0, 0, 3, 'a < b & c > d', IND, 9, 'left'));
  const svg = kit.renderSvg(s);
  assert.match(svg, /a &lt; b &amp; c &gt; d/);
  assert.doesNotMatch(svg, /a < b/);
});

test('an arrow renders as a polygon, never a line', () => {
  const svg = kit.renderSvg(sample());
  assert.match(svg, /<polygon/);
  assert.doesNotMatch(svg, /<line/);
  assert.doesNotMatch(svg, /stroke-dasharray/);
});

test('colours are accepted with or without a leading hash', () => {
  const a = kit.renderSvg(kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.frame(0, 0, 1, 1, '8E6BE6')));
  const b = kit.renderSvg(kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.frame(0, 0, 1, 1, '#8E6BE6')));
  assert.match(a, /#8E6BE6/);
  assert.match(b, /#8E6BE6/);
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio && node --test
```

Expected: FAIL, `Cannot find module '.../slidekit.js'`.

- [ ] **Step 3: Write slidekit**

```js
// demo-studio/skills/create-slides/assets/slidekit.js
'use strict';
/*
  One authoring pass, two backends.

  A slide is authored once by calling the recorder helpers. The recorded ops are
  replayed by renderSvg (the flow-guide preview) and by renderPptx (the deck), so
  both artifacts derive from one coordinate space and cannot drift.

  Coordinates are inches on a 13.333 x 7.5 slide, matching pptxgenjs LAYOUT_WIDE.
  The SVG mirror uses viewBox 0 0 1333 750, the same rectangle scaled by 100.
*/

const LAYOUT = { w: 13.333, h: 7.5 };
const SCALE = 100;
const LABEL_H = 0.28; // inherited from the original label() helper

function hex(color) {
  const c = String(color || '000000').replace(/^#/, '');
  return '#' + c.toUpperCase();
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Rich text may be a plain string or a pptxgenjs text array. Flatten for SVG.
function plainText(rt) {
  if (rt == null) return '';
  if (typeof rt === 'string') return rt;
  if (Array.isArray(rt)) return rt.map((r) => (r && r.text) || '').join('');
  return String(rt.text || '');
}

function recorder(ops) {
  return {
    box(x, y, w, h, opts) { ops.push({ op: 'box', x, y, w, h, opts: opts || {} }); },
    frame(x, y, w, h, color) { ops.push({ op: 'frame', x, y, w, h, color }); },
    arrowR(x, y, w, h, color) { ops.push({ op: 'arrowR', x, y, w, h, color }); },
    arrowD(x, y, w, h, color) { ops.push({ op: 'arrowD', x, y, w, h, color }); },
    label(x, y, w, text, color, size, align) {
      ops.push({ op: 'label', x, y, w, h: LABEL_H, text, color, size, align });
    },
  };
}

function recordSlide(meta, build) {
  const ops = [];
  build(recorder(ops));
  return { eyebrow: meta.eyebrow, title: meta.title, sub: meta.sub, ops };
}

/** Geometry in inches. The single source both backends position from. */
function bboxes(slide) {
  return slide.ops.map((o) => ({
    op: o.op, x: o.x, y: o.y, w: o.w, h: o.h == null ? LABEL_H : o.h,
  }));
}

// Inches to SVG user units. Rounds to 2dp because JS floats are not exact:
// 2.2 * 100 is 220.00000000000003 and 0.28 * 100 is 28.000000000000004, which
// would litter every coordinate in the output. 2dp is far finer than a pixel here.
function u(inches) { return Math.round(inches * SCALE * 100) / 100; }

// Exact for op geometry, rounded for the canvas: u(13.333) is 1333.3000000000002
// in floating point, which would make the viewBox unreadable and untestable.
function viewBoxDim(inches) { return Math.round(inches * SCALE); }

// Block arrows as polygons. Never a <line>: Google Slides drops connectors, and
// the SVG must show what the deck will actually contain.
function arrowRightPoints(x, y, w, h) {
  const shaftH = h * 0.45, headW = Math.min(w * 0.4, h);
  const top = y + (h - shaftH) / 2;
  return [
    [x, top], [x + w - headW, top], [x + w - headW, y],
    [x + w, y + h / 2], [x + w - headW, y + h], [x + w - headW, top + shaftH],
    [x, top + shaftH],
  ].map(([px, py]) => `${u(px)},${u(py)}`).join(' ');
}

function arrowDownPoints(x, y, w, h) {
  const shaftW = w * 0.45, headH = Math.min(h * 0.4, w);
  const left = x + (w - shaftW) / 2;
  return [
    [left, y], [left + shaftW, y], [left + shaftW, y + h - headH],
    [x + w, y + h - headH], [x + w / 2, y + h], [x, y + h - headH],
    [left, y + h - headH],
  ].map(([px, py]) => `${u(px)},${u(py)}`).join(' ');
}

function renderOp(o, palette) {
  const fill = hex((o.opts && o.opts.fill) || palette.panel);
  const line = hex((o.opts && o.opts.line) || palette.border);
  switch (o.op) {
    case 'box':
      return `<rect x="${u(o.x)}" y="${u(o.y)}" width="${u(o.w)}" height="${u(o.h)}" rx="6" `
           + `fill="${fill}" stroke="${line}" stroke-width="1"/>`
           + `<text x="${u(o.x + o.w / 2)}" y="${u(o.y + o.h / 2)}" fill="${hex(palette.txt)}" `
           + `font-family="${palette.body}" font-size="15" text-anchor="middle" `
           + `dominant-baseline="middle">${esc(plainText(o.opts.rt))}</text>`;
    case 'frame':
      return `<rect x="${u(o.x)}" y="${u(o.y)}" width="${u(o.w)}" height="${u(o.h)}" rx="5" `
           + `fill="none" stroke="${hex(o.color)}" stroke-width="1"/>`;
    case 'arrowR':
      return `<polygon points="${arrowRightPoints(o.x, o.y, o.w, o.h)}" fill="${hex(o.color)}"/>`;
    case 'arrowD':
      return `<polygon points="${arrowDownPoints(o.x, o.y, o.w, o.h)}" fill="${hex(o.color)}"/>`;
    case 'label': {
      const anchor = o.align === 'left' ? 'start' : o.align === 'right' ? 'end' : 'middle';
      const tx = o.align === 'left' ? o.x : o.align === 'right' ? o.x + o.w : o.x + o.w / 2;
      return `<text x="${u(tx)}" y="${u(o.y + LABEL_H / 2)}" fill="${hex(o.color)}" `
           + `font-family="${palette.mono}" font-size="${(o.size || 9) * 1.3}" `
           + `font-weight="700" letter-spacing="1" text-anchor="${anchor}" `
           + `dominant-baseline="middle">${esc(o.text)}</text>`;
    }
    default:
      throw new Error(`slidekit: unknown op ${o.op}`);
  }
}

const DEFAULT_PALETTE = {
  bg: '17131F', panel: '241C33', border: '3A3350', txt: 'F4F1FB',
  mut: 'B4AECA', body: 'IBM Plex Sans', mono: 'JetBrains Mono', heading: 'Fraunces',
};

/** Render one slide to a standalone SVG string for a flow-guide preview. */
function renderSvg(slide, palette) {
  const p = Object.assign({}, DEFAULT_PALETTE, palette || {});
  const body = slide.ops.map((o) => renderOp(o, p)).join('\n  ');
  return [
    `<svg viewBox="0 0 ${viewBoxDim(LAYOUT.w)} ${viewBoxDim(LAYOUT.h)}" `
      + `preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%" `
      + `xmlns="http://www.w3.org/2000/svg">`,
    `  <rect x="0" y="0" width="${viewBoxDim(LAYOUT.w)}" height="${viewBoxDim(LAYOUT.h)}" fill="${hex(p.bg)}"/>`,
    `  <text x="60" y="52" fill="${hex('8E6BE6')}" font-family="${p.mono}" `
      + `font-size="14" letter-spacing="2">${esc(slide.eyebrow)}</text>`,
    `  <text x="58" y="105" fill="${hex(p.txt)}" font-family="${p.heading}" `
      + `font-size="42" font-weight="700">${esc(slide.title)}</text>`,
    `  <text x="60" y="150" fill="${hex(p.mut)}" font-family="${p.body}" `
      + `font-size="19">${esc(slide.sub)}</text>`,
    '  ' + body,
    '</svg>',
  ].join('\n');
}

module.exports = {
  LAYOUT, SCALE, LABEL_H,
  recordSlide, bboxes, renderSvg,
  _internal: { hex, esc, plainText, u, renderOp, DEFAULT_PALETTE },
};
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio && node --test
```

Expected: all 9 slidekit tests pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/skills/create-slides/assets/slidekit.js demo-studio/tests/slidekit.test.js
git commit -m "feat: slidekit op recorder and SVG backend

Slides are recorded once as ops in inches and rendered to SVG on a viewBox
that matches the real 13.333x7.5 slide, replacing the 2.30:1 preview frame."
```

---

## Task 10: slidekit PPTX backend and parity

The point of the kit is that the two renderings cannot disagree. This task adds the pptxgenjs backend and a test proving parity without needing pptxgenjs installed.

**Files:**
- Modify: `demo-studio/skills/create-slides/assets/slidekit.js` (add `renderPptx`)
- Modify: `demo-studio/tests/slidekit.test.js` (add the parity suite)
- Modify: `demo-studio/skills/create-slides/assets/build_create_slides.js` (use the kit)

**Interfaces:**
- Consumes: `recordSlide`, `bboxes`, `LAYOUT` from Task 9.
- Produces: `renderPptx(slides, pres, palette) -> pres`, where `pres` is any object satisfying the pptxgenjs surface used here: `addSlide()` returning a slide with `addText(text, opts)`, `addShape(type, opts)`, and a settable `background`; plus `ShapeType` with `roundRect`, `rightArrow`, `downArrow`. Injecting `pres` is what lets the parity test run with a stub.

- [ ] **Step 1: Write the failing test**

Append to `demo-studio/tests/slidekit.test.js`:

```js
// A stub standing in for pptxgenjs, recording what the backend asks for.
function stubPres() {
  const slides = [];
  return {
    ShapeType: { roundRect: 'roundRect', rightArrow: 'rightArrow', downArrow: 'downArrow' },
    slides,
    addSlide() {
      const s = { texts: [], shapes: [], background: null };
      s.addText = (text, opts) => s.texts.push({ text, opts });
      s.addShape = (type, opts) => s.shapes.push({ type, opts });
      slides.push(s);
      return s;
    },
  };
}

test('renderPptx emits one slide per recorded slide', () => {
  const pres = stubPres();
  kit.renderPptx([sample(), sample()], pres);
  assert.strictEqual(pres.slides.length, 2);
});

test('PARITY: every op has the same bbox in both backends', () => {
  const s = sample();
  const pres = stubPres();
  kit.renderPptx([s], pres);
  // renderPptx always emits exactly three header texts first (eyebrow, title,
  // sub). Skip them structurally: filtering by coordinate does not work, because
  // the header sits at x 0.58 and 0.6, inside the range real ops occupy.
  const HEADER_TEXTS = 3;
  const placed = pres.slides[0].texts.slice(HEADER_TEXTS)
    .concat(pres.slides[0].shapes)
    .map((e) => e.opts);
  const boxes = kit.bboxes(s);
  assert.strictEqual(placed.length, boxes.length,
    'the PPTX backend placed a different number of elements than there are ops');
  // Ops are compared by bbox membership, not index: box/label become texts and
  // frame/arrow become shapes, so the concatenated order is not the op order.
  const key = (o) => `${o.x},${o.y},${o.w},${o.h}`;
  const placedKeys = new Set(placed.map(key));
  boxes.forEach((b) => {
    assert.ok(placedKeys.has(key(b)),
      `op ${b.op} bbox ${key(b)} was not placed by the PPTX backend`);
  });
});

test('PARITY: the SVG places the same geometry, scaled', () => {
  const s = sample();
  const svg = kit.renderSvg(s);
  for (const b of kit.bboxes(s)) {
    if (b.op !== 'box' && b.op !== 'frame') continue;
    const u = kit._internal.u;
    assert.match(svg, new RegExp(`x="${u(b.x)}"[^>]*width="${u(b.w)}"`),
      `${b.op} geometry missing from the SVG`);
  }
});

test('the PPTX backend uses block arrows, never connectors', () => {
  const pres = stubPres();
  kit.renderPptx([sample()], pres);
  const types = pres.slides[0].shapes.map((s) => s.type);
  assert.ok(types.includes('rightArrow'));
  assert.ok(!types.some((t) => /onnector|^line$/.test(t)));
});

test('the PPTX backend never emits a dashed line', () => {
  const pres = stubPres();
  kit.renderPptx([sample()], pres);
  const all = JSON.stringify(pres.slides[0]);
  assert.doesNotMatch(all, /prstDash|dashType|"dash"/);
});

test('the PPTX backend strips the leading hash from colours', () => {
  const pres = stubPres();
  kit.renderPptx([kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.frame(1, 1, 2, 2, '#8E6BE6'))], pres);
  const line = pres.slides[0].shapes.find((s) => s.opts.line);
  assert.strictEqual(line.opts.line.color, '8E6BE6');
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio && node --test
```

Expected: FAIL, `kit.renderPptx is not a function`.

- [ ] **Step 3: Write the backend**

Append to `slidekit.js`, before `module.exports`, and add `renderPptx` to the exports:

```js
function bare(color) { return String(color || '000000').replace(/^#/, '').toUpperCase(); }

/**
 * Replay recorded slides into a pptxgenjs presentation.
 * `pres` is injected so tests can pass a stub and prove parity without the dep.
 */
function renderPptx(slides, pres, palette) {
  const p = Object.assign({}, DEFAULT_PALETTE, palette || {});
  const S = pres.ShapeType;
  for (const slide of slides) {
    const s = pres.addSlide();
    s.background = { color: bare(p.bg) };
    s.addText(slide.eyebrow, { x: 0.6, y: 0.42, w: 8, h: 0.3, fontFace: p.mono,
      fontSize: 11, color: bare('8E6BE6'), charSpacing: 2, margin: 0 });
    s.addText(slide.title, { x: 0.58, y: 0.72, w: 12.2, h: 0.9, fontFace: p.heading,
      fontSize: 33, bold: true, color: bare(p.txt), margin: 0 });
    s.addText(slide.sub, { x: 0.6, y: 1.62, w: 11.6, h: 0.5, fontFace: p.body,
      fontSize: 15, color: bare(p.mut), margin: 0 });

    for (const o of slide.ops) {
      switch (o.op) {
        case 'box':
          s.addText(o.opts.rt || '', {
            x: o.x, y: o.y, w: o.w, h: o.h,
            shape: S.roundRect, rectRadius: 0.06,
            fill: { color: bare(o.opts.fill || p.panel) },
            line: { color: bare(o.opts.line || p.border), width: o.opts.lw || 1 },
            align: o.opts.align || 'center',
            valign: o.opts.valign || 'middle',
            margin: o.opts.margin != null ? o.opts.margin : 6,
          });
          break;
        case 'frame':
          s.addShape(S.roundRect, {
            x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.05,
            fill: { color: bare(p.bg) },
            line: { color: bare(o.color), width: 1 },
          });
          break;
        case 'arrowR':
          s.addShape(S.rightArrow, { x: o.x, y: o.y, w: o.w, h: o.h,
            fill: { color: bare(o.color) }, line: { type: 'none' } });
          break;
        case 'arrowD':
          s.addShape(S.downArrow, { x: o.x, y: o.y, w: o.w, h: o.h,
            fill: { color: bare(o.color) }, line: { type: 'none' } });
          break;
        case 'label':
          s.addText(o.text, { x: o.x, y: o.y, w: o.w, h: LABEL_H,
            fontFace: p.mono, fontSize: o.size || 9, color: bare(o.color),
            align: o.align || 'center', bold: true, charSpacing: 1, margin: 0 });
          break;
        default:
          throw new Error(`slidekit: unknown op ${o.op}`);
      }
    }
  }
  return pres;
}
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio && node --test
```

Expected: all pass, in particular the two `PARITY` tests.

- [ ] **Step 5: Port the engagement template onto the kit**

Rewrite `build_create_slides.js` so it authors with the kit and emits both artifacts. Keep the palette loaded from `brand.json` so the PPTX obeys Task 5:

```js
// demo-studio/skills/create-slides/assets/build_create_slides.js
'use strict';
/*
  The per-engagement slide builder. Author one recordSlide block per net-new
  slide. Running this writes BOTH the deck and the preview SVGs, from the same
  coordinates, so the flow guide cannot show a different picture than the deck.

  node build_create_slides.js            -> create-slides.pptx + slide-previews.json
*/
const fs = require('node:fs');
const path = require('node:path');
const pptxgen = require('pptxgenjs');
const kit = require('./slidekit');

const brand = JSON.parse(fs.readFileSync(
  path.join(__dirname, '..', '..', '..', 'shared', 'brand.json'), 'utf8'));
const P = brand.surfaces.pptx;
const palette = {
  bg: nohash(P.bg), panel: nohash(P.panel), border: nohash(P.border),
  txt: nohash(P.txt), mut: nohash(P.mut),
  heading: brand.fonts.heading, body: brand.fonts.body, mono: brand.fonts.mono,
};
// brand.json stores hex with a leading '#', pptxgenjs and the slide lint want it
// without. Normalise once, here, rather than at every call site.
const nohash = (c) => String(c).replace(/^#/, '');
const IND = nohash(P.indigo), CORAL = nohash(P.coral), GREEN = nohash(P.green);

const slides = [
  kit.recordSlide(
    { eyebrow: 'SETUP FLOW 01', title: 'Two lanes, one truth',
      sub: 'Durable state survives; the live worker query does not' },
    (k) => {
      k.box(0.6, 2.4, 4.6, 1.4, { rt: 'PLATFORM LANE', fill: nohash(P.panel) });
      k.arrowR(5.5, 2.9, 0.7, 0.4, IND);
      k.box(6.5, 2.4, 4.6, 1.4, { rt: 'WORKER LANE', fill: nohash(P['coral-fill']) });
      k.label(0.6, 4.0, 4.6, 'SURVIVES A CRASH', GREEN, 9, 'center');
      k.label(6.5, 4.0, 4.6, 'GOES OFFLINE', CORAL, 9, 'center');
    }),
  // Add one recordSlide block per net-new slide.
];

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
kit.renderPptx(slides, pres, palette);
pres.writeFile({ fileName: 'create-slides.pptx' })
  .then((f) => console.log('wrote', f));

// The preview map the flow-guide config pulls preview.body from.
const previews = {};
slides.forEach((s, i) => { previews[`slide-${i + 1}`] = kit.renderSvg(s, palette); });
fs.writeFileSync('slide-previews.json', JSON.stringify(previews, null, 2));
console.log('wrote slide-previews.json with', slides.length, 'preview(s)');
```

- [ ] **Step 6: Build for real and check the artifact**

```bash
cd /Users/dan/code/skills/demo-studio
npm install
node skills/create-slides/assets/build_create_slides.js
~/.asdf/installs/python/3.12.12/bin/python3 -c "
import sys; sys.path.insert(0,'shared')
import guardrails
v = guardrails.check_pptx('create-slides.pptx')
print('pptx violations:', v)
assert v == [], v
print('deck is Google-Slides-safe')
"
```

Expected: the deck builds, `slide-previews.json` is written, and the Task 7 guardrail finds no banned construct.

- [ ] **Step 6b: Update the create-slides reference doc**

`skills/create-slides/references/create-slides-pptx.md` still hardcodes the
sandbox paths in three places. Replace its visual-QA block with the probe:

```bash
. ../../../shared/pptx_tools.sh
PPTX_SKILL="$(find_pptx_skill)" || exit 1
render_preflight || echo "proceeding without visual QA, deck is UNVERIFIED"

node build_create_slides.js
python3 "$PPTX_SKILL/scripts/office/validate.py" create-slides.pptx
python3 "$PPTX_SKILL/scripts/office/soffice.py" --headless --convert-to pdf create-slides.pptx
pdftoppm -jpeg -r 150 create-slides.pdf slide      # then VIEW every slide-N.jpg
```

Change its closing line from "read `/mnt/skills/public/pptx/SKILL.md`" to "read
the pptx skill's SKILL.md at the path `find_pptx_skill` resolves". Verify no
`/mnt` reference survives anywhere:

```bash
cd /Users/dan/code/skills/demo-studio && grep -rn "/mnt/skills" . --exclude-dir=node_modules || echo "clean"
```

- [ ] **Step 7: Run the render preflight**

```bash
cd /Users/dan/code/skills/demo-studio
. shared/pptx_tools.sh
render_preflight || echo "(expected on this machine: visual QA cannot run)"
```

Expected: the unverified banner. Install LibreOffice and poppler if you want the visual pass now; otherwise this is exactly the degraded path Task 3 built, and the deck must be reported as unverified.

- [ ] **Step 8: Commit**

```bash
cd /Users/dan/code/skills
echo "demo-studio/node_modules/" >> .gitignore
echo "demo-studio/create-slides.pptx" >> .gitignore
echo "demo-studio/slide-previews.json" >> .gitignore
git add .gitignore demo-studio/skills/create-slides/assets demo-studio/tests/slidekit.test.js \
        demo-studio/package.json
git commit -m "feat: slidekit PPTX backend with proven parity to the SVG

Both backends replay the same recorded ops, and the parity test asserts every
bounding box matches. The engagement template now emits the deck and the
preview SVGs from one authoring pass."
```

---

## Task 11: Slide lint

Catch authoring mistakes at the source, with a line the author can fix, before anything renders.

**Files:**
- Create: `demo-studio/skills/create-slides/assets/lint_slides.js`
- Create: `demo-studio/tests/lint_slides.test.js`

**Interfaces:**
- Consumes: `LAYOUT`, `bboxes`, `LABEL_H` from slidekit.
- Produces: `lintSlides(slides) -> [{slide, op, rule, detail}]` and `formatFindings(findings) -> string`. Rules: `off-canvas`, `em-dash`, `hash-in-hex`, `zero-size`.

- [ ] **Step 1: Write the failing test**

```js
// demo-studio/tests/lint_slides.test.js
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

const base = path.join(__dirname, '..', 'skills', 'create-slides', 'assets');
const kit = require(path.join(base, 'slidekit.js'));
const { lintSlides, formatFindings } = require(path.join(base, 'lint_slides.js'));

const one = (build) => [kit.recordSlide({ eyebrow: 'E', title: 'T', sub: 'S' }, build)];

test('a clean slide produces no findings', () => {
  assert.deepStrictEqual(lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'ok' }))), []);
});

test('flags a box running off the right edge', () => {
  const f = lintSlides(one((k) => k.box(12, 1, 2, 1, { rt: 'wide' })));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'off-canvas');
  assert.match(f[0].detail, /13\.333/);
});

test('flags a box running off the bottom edge', () => {
  const f = lintSlides(one((k) => k.box(1, 7, 2, 1, { rt: 'low' })));
  assert.strictEqual(f[0].rule, 'off-canvas');
  assert.match(f[0].detail, /7\.5/);
});

test('flags a negative origin', () => {
  assert.strictEqual(lintSlides(one((k) => k.box(-0.5, 1, 2, 1, {})))[0].rule, 'off-canvas');
});

test('flags an em dash in slide text', () => {
  const f = lintSlides(one((k) => k.label(1, 1, 3, 'fast — durable', 'IND', 9, 'center')));
  assert.strictEqual(f[0].rule, 'em-dash');
});

test('flags an em dash in box rich text', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'a — b' })));
  assert.strictEqual(f[0].rule, 'em-dash');
});

test('flags a colour written with a leading hash', () => {
  const f = lintSlides(one((k) => k.frame(1, 1, 2, 1, '#8E6BE6')));
  assert.strictEqual(f[0].rule, 'hash-in-hex');
});

test('flags a zero-size shape', () => {
  assert.strictEqual(lintSlides(one((k) => k.box(1, 1, 0, 1, {})))[0].rule, 'zero-size');
});

test('findings name the slide index and the op index', () => {
  const f = lintSlides(one((k) => { k.box(1, 1, 2, 1, {}); k.box(99, 1, 2, 1, {}); }));
  assert.strictEqual(f[0].slide, 1);
  assert.strictEqual(f[0].op, 2);
});

test('formatFindings is one line per finding', () => {
  const f = lintSlides(one((k) => { k.box(99, 1, 2, 1, {}); k.frame(1, 1, 2, 1, '#FFF000'); }));
  assert.strictEqual(formatFindings(f).trim().split('\n').length, 2);
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio && node --test tests/lint_slides.test.js
```

Expected: FAIL, cannot find `lint_slides.js`.

- [ ] **Step 3: Write the linter**

```js
// demo-studio/skills/create-slides/assets/lint_slides.js
'use strict';
/*
  Author-time checks on recorded slides. These catch the mistakes that only show
  up when you finally look at a rendered image, which on a machine without
  LibreOffice may be never.
*/
const kit = require('./slidekit');

const EM_DASH = '—';

function textOf(o) {
  if (o.op === 'label') return String(o.text == null ? '' : o.text);
  if (o.op === 'box') return kit._internal.plainText(o.opts && o.opts.rt);
  return '';
}

function coloursOf(o) {
  const out = [];
  if (o.color != null) out.push(o.color);
  if (o.opts) {
    if (o.opts.fill != null) out.push(o.opts.fill);
    if (o.opts.line != null) out.push(o.opts.line);
  }
  return out;
}

function lintSlides(slides) {
  const findings = [];
  slides.forEach((slide, si) => {
    const boxes = kit.bboxes(slide);
    slide.ops.forEach((o, oi) => {
      const b = boxes[oi];
      const at = { slide: si + 1, op: oi + 1 };

      if (b.w <= 0 || b.h <= 0) {
        findings.push(Object.assign({}, at, { rule: 'zero-size',
          detail: `${o.op} has width ${b.w} and height ${b.h}` }));
      } else if (b.x < 0 || b.y < 0
                 || b.x + b.w > kit.LAYOUT.w || b.y + b.h > kit.LAYOUT.h) {
        findings.push(Object.assign({}, at, { rule: 'off-canvas',
          detail: `${o.op} spans x ${b.x} to ${(b.x + b.w).toFixed(3)} and `
                + `y ${b.y} to ${(b.y + b.h).toFixed(3)}, `
                + `slide is ${kit.LAYOUT.w} by ${kit.LAYOUT.h}` }));
      }

      if (textOf(o).includes(EM_DASH)) {
        findings.push(Object.assign({}, at, { rule: 'em-dash',
          detail: 'use a comma or restructure' }));
      }

      for (const c of coloursOf(o)) {
        if (typeof c === 'string' && c.startsWith('#')) {
          findings.push(Object.assign({}, at, { rule: 'hash-in-hex',
            detail: `pptxgenjs wants ${c.slice(1)}, not ${c}` }));
        }
      }
    });
  });
  return findings;
}

function formatFindings(findings) {
  return findings
    .map((f) => `  slide ${f.slide} op ${f.op}  ${f.rule.padEnd(12)} ${f.detail}`)
    .join('\n');
}

module.exports = { lintSlides, formatFindings };
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio && node --test
```

Expected: all pass.

- [ ] **Step 5: Gate the build on the lint**

In `build_create_slides.js`, immediately after the `slides` array and before creating the presentation:

```js
const { lintSlides, formatFindings } = require('./lint_slides');
const findings = lintSlides(slides);
if (findings.length) {
  console.error(`slide lint failed with ${findings.length} finding(s):`);
  console.error(formatFindings(findings));
  process.exit(1);
}
```

- [ ] **Step 6: Verify the gate with a seeded fault**

Temporarily change one `recordSlide` box to `k.box(12, 1, 2, 1, {...})`, run the builder, confirm it exits 1 naming the slide and op, then revert.

```bash
cd /Users/dan/code/skills/demo-studio
node skills/create-slides/assets/build_create_slides.js; echo "exit=$?"
```

- [ ] **Step 7: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/skills/create-slides/assets/lint_slides.js \
        demo-studio/skills/create-slides/assets/build_create_slides.js \
        demo-studio/tests/lint_slides.test.js
git commit -m "feat: lint recorded slides before rendering

Off-canvas geometry, em dashes, hash-prefixed hex and zero-size shapes fail
the build with the slide and op named, which matters most on machines where
the visual QA loop cannot run."
```

---

## Task 12: The discovery artifact

Pipeline stages 1 to 4 currently produce nothing durable. Giving them an artifact with signal ids is what makes traces-to checkable in Task 13.

**Files:**
- Create: `demo-studio/skills/demo-discovery/assets/schema_discovery.py`
- Create: `demo-studio/skills/demo-discovery/assets/build_discovery.py`
- Create: `demo-studio/skills/demo-discovery/assets/examples/discovery.example.json`
- Create: `demo-studio/skills/demo-discovery/references/discovery-format.md`
- Create: `demo-studio/tests/test_discovery.py`

**Interfaces:**
- Consumes: `validate_config`, `guardrails` from earlier tasks.
- Produces: `discovery.json` as the durable artifact, and `build_discovery.py CONFIG.json OUT.md` rendering the readable version. The module exposes `DiscoveryError(Exception)`, `check_signals(cfg)` raising it when the signal set is internally inconsistent, and `render(cfg) -> str` returning the Markdown. Signal ids match `^D\d+$`. Each signal has `id`, `kind` (`"grounded"` or `"inferred"`), `text`; a grounded signal also has `quote` and `attribution`; an inferred signal may list `exercises` (ids it was designed to exercise).

- [ ] **Step 1: Write the failing test**

```python
# demo-studio/tests/test_discovery.py
"""The discovery artifact: schema, id rules, and the readable render."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "skills", "demo-discovery", "assets")
sys.path.insert(0, os.path.join(ROOT, "shared"))
sys.path.insert(0, ASSETS)

import validate_config as vc  # noqa: E402
import schema_discovery  # noqa: E402
import build_discovery  # noqa: E402

EXAMPLE = os.path.join(ASSETS, "examples", "discovery.example.json")


def load_example():
    with open(EXAMPLE) as f:
        return json.load(f)


class TestSchema(unittest.TestCase):
    def test_the_example_validates(self):
        self.assertEqual(vc.validate(load_example(), schema_discovery.SCHEMA), [])

    def test_a_signal_needs_an_id_and_a_kind(self):
        cfg = load_example()
        del cfg["signals"][0]["kind"]
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("signals[0].kind" in e for e in errors), errors)

    def test_kind_is_restricted(self):
        cfg = load_example()
        cfg["signals"][0]["kind"] = "maybe"
        errors = vc.validate(cfg, schema_discovery.SCHEMA)
        self.assertTrue(any("grounded" in e for e in errors), errors)


class TestSignalRules(unittest.TestCase):
    def test_ids_are_unique(self):
        cfg = load_example()
        cfg["signals"].append(dict(cfg["signals"][0]))
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_ids_match_the_expected_shape(self):
        cfg = load_example()
        cfg["signals"][0]["id"] = "sig-1"
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("D1", str(ctx.exception))

    def test_a_grounded_signal_must_carry_a_quote_and_attribution(self):
        cfg = load_example()
        grounded = next(s for s in cfg["signals"] if s["kind"] == "grounded")
        del grounded["quote"]
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("quote", str(ctx.exception))

    def test_an_inferred_signal_needs_no_quote(self):
        cfg = load_example()
        inferred = [s for s in cfg["signals"] if s["kind"] == "inferred"]
        self.assertTrue(inferred, "the example must include an inferred signal")
        build_discovery.check_signals(cfg)  # must not raise

    def test_exercises_must_reference_real_signals(self):
        cfg = load_example()
        inferred = next(s for s in cfg["signals"] if s["kind"] == "inferred")
        inferred["exercises"] = ["D99"]
        with self.assertRaises(build_discovery.DiscoveryError) as ctx:
            build_discovery.check_signals(cfg)
        self.assertIn("D99", str(ctx.exception))


class TestRender(unittest.TestCase):
    def test_renders_markdown_naming_every_signal(self):
        cfg = load_example()
        md = build_discovery.render(cfg)
        for signal in cfg["signals"]:
            self.assertIn(signal["id"], md)

    def test_grounded_and_inferred_are_visibly_separated(self):
        md = build_discovery.render(load_example())
        self.assertIn("GROUNDED", md.upper())
        self.assertIn("INFERRED", md.upper())

    def test_no_em_dashes_in_the_render(self):
        self.assertNotIn("—", build_discovery.render(load_example()))

    def test_cli_writes_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "discovery.md")
            proc = subprocess.run(
                [sys.executable, os.path.join(ASSETS, "build_discovery.py"), EXAMPLE, out],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_discovery -v
```

Expected: FAIL, `No module named 'schema_discovery'`.

- [ ] **Step 3: Write the example artifact**

Public-safe throughout: roles, never names.

```json
{
  "engagement": "example-2026-09",
  "signals": [
    {
      "id": "D1",
      "kind": "grounded",
      "text": "No way to distinguish a dead worker from a slow job",
      "quote": "we cannot tell if a worker died or the job is just slow",
      "attribution": "platform lead"
    },
    {
      "id": "D2",
      "kind": "grounded",
      "text": "Retries are hand rolled per service and drift",
      "quote": "every team wrote their own retry loop and none of them agree",
      "attribution": "staff engineer"
    },
    {
      "id": "D3",
      "kind": "grounded",
      "text": "Regulated environment, self hosted only",
      "quote": "we cannot send claim data to a vendor cloud",
      "attribution": "security architect"
    },
    {
      "id": "D4",
      "kind": "inferred",
      "text": "Claims adjudication domain skin for the demo",
      "exercises": ["D1", "D3"]
    },
    {
      "id": "D5",
      "kind": "inferred",
      "text": "Kill a worker mid run to make durability visible",
      "exercises": ["D1", "D2"]
    }
  ],
  "demo_fit": [
    {"demo": "Durable pipeline", "why": "shows D1 directly", "verdict": "lead"},
    {"demo": "Saga rollback", "why": "answers D2 without a new build", "verdict": "second"},
    {"demo": "Cloud onboarding", "why": "self hosted only, D3", "verdict": "skip"}
  ],
  "session": {
    "pitch": false,
    "deployment": "self-hosted",
    "beats": [
      ["00:00", "Open and frame", 5],
      ["00:05", "Model the problem", 10],
      ["00:15", "Live demo", 25],
      ["00:40", "Handoff and next steps", 10]
    ]
  },
  "fork": {
    "choice": "v1",
    "why": "first session, independent failure surfaces beat fidelity"
  }
}
```

- [ ] **Step 4: Write the schema**

```python
# demo-studio/skills/demo-discovery/assets/schema_discovery.py
"""Schema for discovery.json. See references/discovery-format.md."""

_SIGNAL = {
    "type": "object",
    "required": ["id", "kind", "text"],
    "properties": {
        "id": {"type": "string", "minLength": 2},
        "kind": {"type": "string", "enum": ["grounded", "inferred"]},
        "text": {"type": "string", "minLength": 1},
        "quote": {"type": "string"},
        "attribution": {"type": "string"},
        "exercises": {"type": "array", "items": {"type": "string"}},
    },
}

SCHEMA = {
    "type": "object",
    "required": ["engagement", "signals"],
    "properties": {
        "engagement": {"type": "string", "minLength": 1},
        "signals": {"type": "array", "items": _SIGNAL},
        "demo_fit": {"type": "array", "items": {
            "type": "object",
            "required": ["demo", "why", "verdict"],
            "properties": {
                "demo": {"type": "string"},
                "why": {"type": "string"},
                "verdict": {"type": "string", "enum": ["lead", "second", "skip"]},
            },
        }},
        "session": {"type": "object"},
        "fork": {"type": "object"},
    },
}
```

- [ ] **Step 5: Write the builder**

```python
#!/usr/bin/env python3
# demo-studio/skills/demo-discovery/assets/build_discovery.py
"""Render discovery.json to a readable Markdown record.

The JSON is the durable artifact that later stages reference by signal id; this
Markdown is the version a human reads. Stdlib only, Python 3.9 compatible.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "shared"))
import guardrails       # noqa: E402
import validate_config  # noqa: E402

import schema_discovery  # noqa: E402

ID_RE = re.compile(r"^D\d+$")


class DiscoveryError(Exception):
    """Raised when the signal set is internally inconsistent."""


def check_signals(cfg):
    """Rules the schema dialect cannot express."""
    seen = set()
    problems = []
    for i, signal in enumerate(cfg["signals"]):
        sid = signal["id"]
        if not ID_RE.match(sid):
            problems.append("signals[%d].id: %r must look like D1, D2, D3" % (i, sid))
        if sid in seen:
            problems.append("signals[%d].id: duplicate id %r" % (i, sid))
        seen.add(sid)
        if signal["kind"] == "grounded":
            for field in ("quote", "attribution"):
                if not signal.get(field):
                    problems.append(
                        "signals[%d] (%s): a grounded signal needs %s, "
                        "otherwise it is inferred" % (i, sid, field))
    for i, signal in enumerate(cfg["signals"]):
        for ref in signal.get("exercises", ()):
            if ref not in seen:
                problems.append(
                    "signals[%d].exercises: %s does not exist" % (i, ref))
    if problems:
        raise DiscoveryError("%d problem(s):\n  %s" % (len(problems), "\n  ".join(problems)))


def render(cfg):
    """Markdown, grounded signals first so provenance reads at a glance."""
    out = ["# Discovery record: %s" % cfg["engagement"], ""]

    for kind, heading in (("grounded", "Grounded (they said it)"),
                          ("inferred", "Inferred (we designed it)")):
        rows = [s for s in cfg["signals"] if s["kind"] == kind]
        if not rows:
            continue
        out += ["## %s" % heading, ""]
        for s in rows:
            out.append("**%s** %s" % (s["id"], s["text"]))
            if s.get("quote"):
                out.append('> "%s"' % s["quote"])
                out.append("> %s" % s.get("attribution", "unattributed"))
            if s.get("exercises"):
                out.append("Exercises: %s" % ", ".join(s["exercises"]))
            out.append("")

    if cfg.get("demo_fit"):
        out += ["## Demo fit", "", "| Demo | Why | Verdict |", "|---|---|---|"]
        for row in cfg["demo_fit"]:
            out.append("| %s | %s | %s |" % (row["demo"], row["why"], row["verdict"]))
        out.append("")

    session = cfg.get("session") or {}
    if session.get("beats"):
        out += ["## Session design", "",
                "Pitch: %s. Deployment: %s." % (
                    "yes" if session.get("pitch") else "no",
                    session.get("deployment", "unstated")),
                "", "| Start | Beat | Minutes |", "|---|---|---|"]
        for start, name, mins in session["beats"]:
            out.append("| %s | %s | %s |" % (start, name, mins))
        out.append("")

    fork = cfg.get("fork") or {}
    if fork:
        out += ["## v1 or v2", "",
                "Choice: **%s**. %s" % (fork.get("choice", "unstated"),
                                        fork.get("why", "")), ""]
    return "\n".join(out)


def main():
    cfg_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "discovery.md"
    with open(cfg_path) as f:
        cfg = json.load(f)
    validate_config.enforce(cfg, schema_discovery.SCHEMA,
                            name=os.path.basename(cfg_path))
    check_signals(cfg)
    guardrails.enforce(guardrails.check_tree(
        cfg, allowlist=cfg.get("allow_words", ()), banned=cfg.get("banned_terms", ())))
    text = render(cfg)
    with open(out_path, "w") as f:
        f.write(text)
    print("wrote %s with %d signal(s)" % (out_path, len(cfg["signals"])))


if __name__ == "__main__":
    try:
        main()
    except (validate_config.ConfigError, guardrails.GuardrailError, DiscoveryError) as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)
```

- [ ] **Step 6: Write the format reference**

`references/discovery-format.md` documents the fields, the `D\d+` id convention, the grounded-versus-inferred rule, and states that later stages reference these ids from their `traces` fields.

- [ ] **Step 7: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  $PY -m unittest discover -s tests -v
done
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/skills/demo-discovery demo-studio/tests/test_discovery.py
git commit -m "feat: discovery becomes a durable artifact with signal ids

Stages 1 to 4 now emit discovery.json plus a readable render. Grounded signals
must carry a quote and attribution; inferred ones declare what they exercise."
```

---

## Task 13: Verifiable traces-to

`traces` is free text that nothing checks. Pointing it at signal ids turns the skill's load-bearing discipline into something a build can enforce.

**Files:**
- Create: `demo-studio/shared/traces.py`
- Create: `demo-studio/tests/test_traces.py`
- Modify: both guide generators (resolve traces when `discovery` is set)

**Interfaces:**
- Consumes: `Violation` from `guardrails`.
- Produces: `shared/traces.py` exposing
  - `REF_RE`, the compiled pattern `\bD\d+\b`,
  - `refs(text) -> list[str]`, ids found in order, deduplicated,
  - `signal_ids(discovery) -> set[str]`,
  - `check_traces(config, discovery) -> list[Violation]` walking every `traces` field,
  - `load_discovery(path) -> dict`.
  Checks `unresolved-trace` (an id with no matching signal) and `untraced` (a `traces` field containing no id at all, reported as a warning-level violation with check `untraced`).

- [ ] **Step 1: Write the failing test**

```python
# demo-studio/tests/test_traces.py
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_traces -v
```

Expected: FAIL, `No module named 'traces'`.

- [ ] **Step 3: Write the implementation**

```python
# demo-studio/shared/traces.py
"""Resolve traces-to references against the discovery record.

Every flow-guide card and presenter-guide slide claims to trace back to a
discovery signal. Free text made that unverifiable. Signal ids make it a
resolvable reference, so a card that traces to nothing is a build finding.
"""
import json
import re

from guardrails import Violation

REF_RE = re.compile(r"\bD\d+\b")


def refs(text):
    """Signal ids in a string, in order, deduplicated."""
    if not isinstance(text, str):
        return []
    out = []
    for match in REF_RE.findall(text):
        if match not in out:
            out.append(match)
    return out


def signal_ids(discovery):
    return {s["id"] for s in (discovery or {}).get("signals", ())}


def load_discovery(path):
    with open(path) as f:
        return json.load(f)


def _walk(obj, known, path, out):
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = key if not path else "%s.%s" % (path, key)
            if key == "traces" and isinstance(value, str):
                found = refs(value)
                if not found:
                    out.append(Violation(
                        "untraced", child,
                        "no signal id, every card should trace to a D-number"))
                for ref in found:
                    if ref not in known:
                        out.append(Violation(
                            "unresolved-trace", child, "%s does not exist" % ref))
            else:
                _walk(value, known, child, out)
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            _walk(value, known, "%s[%d]" % (path, i), out)


def check_traces(config, discovery):
    """Return violations for traces fields. No discovery record means no check."""
    if not discovery:
        return []
    out = []
    _walk(config, signal_ids(discovery), "", out)
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  $PY -m unittest tests.test_traces -v
done
```

Expected: all pass.

- [ ] **Step 5: Wire it into both generators**

After the guardrail call in each generator's `main`:

```python
import traces as traces_mod
...
    discovery = None
    if cfg.get("discovery"):
        discovery_path = cfg["discovery"]
        if not os.path.isabs(discovery_path):
            discovery_path = os.path.join(os.path.dirname(cfg_path), discovery_path)
        discovery = traces_mod.load_discovery(discovery_path)
    found = traces_mod.check_traces(cfg, discovery)
    if found:
        guardrails.enforce(found)
    elif discovery is None:
        sys.stderr.write(
            "note: no 'discovery' field in the config, so traces-to was NOT checked\n")
```

The note matters. A silently skipped check reads exactly like a passing one, and the whole point of this task is that the discipline stops being assumed.

- [ ] **Step 6: Verify end to end**

```bash
cd /Users/dan/code/skills/demo-studio
PY=~/.asdf/installs/python/3.12.12/bin/python3
# Without a discovery field: builds, but says the check did not run.
$PY skills/deck-flow-guide/assets/build_flow_guide.py \
    skills/deck-flow-guide/assets/examples/flow_guide.example.json /tmp/f.html
# With one: point the example at the discovery example and add a bad ref.
$PY - <<'EOF'
import json, pathlib
p = pathlib.Path("skills/deck-flow-guide/assets/examples/flow_guide.example.json")
cfg = json.loads(p.read_text())
cfg["discovery"] = "../../../demo-discovery/assets/examples/discovery.example.json"
cfg["acts"][0]["cards"][0]["traces"] = "D99"
pathlib.Path("/tmp/traced.json").write_text(json.dumps(cfg))
EOF
$PY skills/deck-flow-guide/assets/build_flow_guide.py /tmp/traced.json /tmp/f2.html; echo "exit=$?"
```

Expected: the first run builds and prints the "NOT checked" note. The second exits 1 with `unresolved-trace  acts[0].cards[0].traces  D99 does not exist`.

- [ ] **Step 7: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/shared/traces.py demo-studio/tests/test_traces.py \
        demo-studio/skills/deck-flow-guide/assets/build_flow_guide.py \
        demo-studio/skills/presenter-guide/assets/build_presenter_guide.py
git commit -m "feat: resolve traces-to against the discovery record

A card claiming to trace to D9 now fails when D9 does not exist, and a config
with no discovery record says so rather than silently passing."
```

---

## Task 14: Router and worker descriptions

Descriptions are the interface. This task writes all six, obeying the rule that a description states triggering conditions and never summarizes a workflow.

**Files:**
- Modify: all six `demo-studio/skills/*/SKILL.md`
- Create: `demo-studio/tests/test_descriptions.py`
- Create: `demo-studio/skills/*/QUICKSTART.md` sections (folded into each SKILL.md)

**Interfaces:**
- Consumes: the layout from Task 4.
- Produces: six skills whose descriptions are disjoint enough that a direct worker request does not get swallowed by the router.

- [ ] **Step 1: Write the failing test**

```python
# demo-studio/tests/test_descriptions.py
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest tests.test_descriptions -v
```

Expected: FAIL on the Task 4 stubs.

- [ ] **Step 3: Write the router**

```markdown
---
name: demo-studio
description: >-
  Use when someone shares a customer or discovery call transcript and wants demo
  or enablement work, when they ask for the whole pre-sales set for an upcoming
  session, when they say "demo studio", or when they want demo help but it is not
  clear which piece they need. Not for a request that names one artifact: those
  have their own skills.
---

# Demo Studio

Router for the pre-sales pipeline. Figure out where the user is, then hand off.
Do not do the work here, and do not force a stage nobody asked for.

## Entry points

| They say | Go to |
|---|---|
| "Here's a transcript" | `demo-studio:demo-discovery`, then onward |
| "Which demo should we lead with" | `demo-studio:demo-discovery` |
| "Spec the demo" | `demo-studio:build-spec` |
| "Piece the deck for this room" | `demo-studio:deck-flow-guide` |
| "Build the net-new slides" | `demo-studio:create-slides` |
| "Make the presenter guide" | `demo-studio:presenter-guide` |
| "I know the demo, build the deck and guides" | flow guide, create slides, presenter guide |
| Genuinely unclear | Ask which stage. Do not guess. |

## Sequencing

Full run: discovery, build spec, flow guide, create slides, presenter guide.
Build one artifact at a time and show it before starting the next.

## Recommend, then lock

At each hinge, commit to a recommendation and get a small set of decisions locked
before building. Do not present an exhaustive menu.

## Disciplines

Read `../../shared/grounding.md`. Provenance, reference wins, public safe, no
AI tells. The mechanical rules are enforced by `../../shared/guardrails.py`, so a
violation fails the build rather than needing to be remembered.
```

- [ ] **Step 4: Write the five worker descriptions**

```yaml
# demo-discovery
description: >-
  Use when a call transcript needs reading for demo signals, when someone asks
  which demo to lead with or skip, who will be in the room, what stack or
  constraints the customer stated, or wants a demo fit analysis, a session beat
  sheet, or a grounded versus inferred record of what was actually said.

# build-spec
description: >-
  Use when someone wants a build spec, wants a customer demo specified so a
  coding agent can build it end to end, or asks what to hand an engineer to make
  the demo real.

# deck-flow-guide
description: >-
  Use when someone wants a flow guide, wants an existing deck reordered or pieced
  together for a specific room, asks which slides to pull and which to build, or
  wants a cut list for when the session runs short.

# create-slides
description: >-
  Use when someone wants net-new slides built, a dark PPTX that drops into an
  aggregate deck, slide mockups or diagrams for a demo deck, or wants existing
  create slides tweaked and re-rendered.

# presenter-guide
description: >-
  Use when someone wants a presenter guide, speaker notes, a teleprompter script,
  per-slide talking points or questions to ask, a run of show, or wants a demo
  runbook turned into a live walkthrough for delivering a deck.
```

Each worker body keeps its stage content lifted from the old SKILL.md, points at its own `references/` and `assets/`, includes the copy-edit-run block from the old QUICKSTART, and reads `../../shared/grounding.md`.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/dan/code/skills/demo-studio
~/.asdf/installs/python/3.12.12/bin/python3 -m unittest discover -s tests -v
```

Expected: all pass, including `test_the_router_does_not_claim_the_workers_artifacts`.

- [ ] **Step 6: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/skills demo-studio/tests/test_descriptions.py
git commit -m "feat: write the router and five worker descriptions

Each description states triggering conditions only. The router deliberately
does not advertise the workers' artifact nouns, so a direct request for a
presenter guide reaches the skill that builds one."
```

---

## Task 15: Router behaviour tests

The one genuinely behavioural question, and the only task authorized to spawn subagents. Everything up to here is mechanically verifiable; routing is not.

**Files:**
- Create: `demo-studio/tests/router-scenarios.md`

**Interfaces:**
- Consumes: the six descriptions from Task 14.
- Produces: a recorded pass or fail per scenario, and description edits where a scenario fails.

- [ ] **Step 1: Write the scenarios**

```markdown
# Router behaviour scenarios

Dispatch each prompt to a fresh subagent with the demo-studio plugin available and
nothing else from this conversation. Record which skill fired first.

| # | Prompt | Expected |
|---|---|---|
| R1 | "Here's the transcript from our call with the platform team." (plus a transcript) | router fires, offers the full pipeline |
| R2 | "Make me a presenter guide for this deck." | presenter-guide fires directly, no discovery stage forced |
| R3 | "Reorder this deck for a security team audience." | deck-flow-guide fires |
| R4 | "Add the demo walkthrough to the guide." | presenter-guide, demo block only |
| R5 | "Help me with a customer demo." | router fires and ASKS which stage, does not guess |
| R6 | "I know the demo already, build the deck and the guides." | flow guide, create slides, presenter guide. Discovery and build spec skipped |

R2 and R6 are the ones the monolith could not get right by construction: with one
description there was nothing for a direct request to match against.
```

- [ ] **Step 2: Run the baseline (RED)**

Before relying on the new descriptions, run R1 to R6 against a subagent with only
the pre-restructure monolith available. Record verbatim which skill fired and what
the agent said. Expect R2, R4 and R6 to over-trigger into the full pipeline. This
is the failing test that justifies the split.

- [ ] **Step 3: Run the scenarios against the new descriptions (GREEN)**

Dispatch each of R1 to R6 as a separate subagent task. For each, record: which skill
fired, whether it asked or guessed, and the first two sentences of the response.

- [ ] **Step 4: Fix any misroute at the description, not the body**

A scenario that routes wrong is a description problem. Adjust the triggering
conditions of the skill that should have fired, or narrow the one that wrongly did,
then re-run that scenario plus R1 and R5 to confirm nothing regressed. Descriptions
are load bearing for every other skill's discoverability, so re-check the whole set
after any edit.

- [ ] **Step 5: Record the results**

Append a results table to `tests/router-scenarios.md` with the date, the outcome per
scenario, and any description change made in response.

- [ ] **Step 6: Run the entire suite one last time**

```bash
cd /Users/dan/code/skills/demo-studio
for PY in /usr/bin/python3 ~/.asdf/installs/python/3.12.12/bin/python3; do
  echo "== $PY"; $PY -m unittest discover -s tests -v || exit 1
done
node --test
bash tests/test_pptx_tools.sh
```

Expected: everything green on both interpreters.

- [ ] **Step 7: Commit**

```bash
cd /Users/dan/code/skills
git add demo-studio/tests/router-scenarios.md demo-studio/skills
git commit -m "test: record router behaviour scenarios and their results

R1 to R6 dispatched to fresh subagents against baseline and the new
descriptions. Misroutes were fixed in descriptions, not skill bodies."
```

---

## Verification matrix

Maps the spec's gates to the task that satisfies each.

| Spec gate | Task | How it is checked |
|---|---|---|
| V1 both generators on 3.9 and 3.12 | 2 | `TestInterpreterFloor` plus the two-interpreter loop in every task |
| V2 output diffs reviewed, not assumed | 1, 5 | golden baseline captured before edits; re-baselined only after a reviewed diff and a browser check |
| V3 seeded guardrail violations fail | 6, 7 | `test_guardrails.py` plus the seeded-violation step |
| V4 configs rejected with a path | 8 | `test_validate_config.py` plus the by-hand error check |
| V5 one hex change propagates | 5 | `test_brand.py`, `TestNoHexLiteralsRemain` |
| V6 SVG and PPTX bboxes agree | 10 | the two `PARITY` tests |
| V7 unresolvable traces reported | 13 | `test_traces.py` plus the end-to-end check |
| V8 missing render tools warn loudly | 3 | `test_pptx_tools.sh` case 5, the banner assertion |
| V9 frontmatter valid, no workflow summaries | 4, 14 | `test_layout.py`, `test_descriptions.py` |
| R1 to R6 routing | 15 | subagent scenarios, recorded |

## Open item carried from the spec

Installation is still undecided: a local marketplace entry versus symlinking
`skills/*` into `~/.claude/skills/`. Nothing in this plan depends on the answer,
but the plugin is not usable outside this repo until it is settled. Resolve it
after Task 15.
