# demo-studio

A Claude Code plugin that turns a customer discovery call into the set of things
you need to walk into the next meeting: a demo build spec, a deck flow guide, the
net-new slides as a dark PPTX, and a presenter guide with a live-demo run of show.

Six skills. You can run the whole pipeline from a transcript, or ask for one
artifact by name and skip the rest.

## Install

```bash
claude plugin marketplace add <owner>/<repo>
claude plugin install demo-studio@dan-skills
```

That is all it needs. The plugin is pure Python and JavaScript with one npm
dependency, used by a single skill.

## Use it

You do not need to name a skill. Say what you want and the right one fires.

Paste a transcript and ask for the set:

> Here's the transcript from our call with the platform team. I need the full
> set for a session next week.

Or ask for one piece:

> Make me a presenter guide for this deck.
> Reorder this deck for a security team audience.
> Which demo should we lead with?

If it is genuinely unclear what you want, the router asks rather than guessing.

## The six skills

| Skill | What it does | Emits |
|---|---|---|
| `demo-studio` | Router. Works out which stage you are at and hands off. Holds the sequencing and the recommend-then-lock hinge. | nothing, it delegates |
| `demo-discovery` | Reads the transcript. Who is really in the room, their stack, their pains quoted, constraints, which demo to lead with, a beat sheet, and the v1-versus-v2 call. | `discovery.json`, `discovery.md` |
| `build-spec` | Specifies the demo so a coding agent can build it end to end. | `BUILD_SPEC.md` |
| `deck-flow-guide` | Pieces a deck for one specific room: which existing slides to pull, named exactly, and which to build. | `flow-guide.html` |
| `create-slides` | Builds the net-new slides as a dark, Google-Slides-safe PPTX, plus the SVG previews the flow guide shows. | `create-slides.pptx`, `slide-previews.json` |
| `presenter-guide` | Per-slide talking points, a teleprompter script, questions to ask and expect back, and an optional live-demo run of show. | `presenter-guide.html` |

## What makes it different from a prompt

The skill states a set of disciplines: quote what the customer said and label what
you designed, keep everything public-safe, no filler, Google-Slides-safe shapes,
readable contrast. Stating them is easy. This plugin **enforces** them, so a
violation fails a build instead of depending on anyone remembering:

- **Provenance is checkable.** Every discovery signal gets an id. A flow-guide
  card or presenter-guide slide that claims to trace back to one is resolved
  against the real record: an id that does not exist fails the build, and free
  text warns. A config with no discovery record says so rather than passing
  quietly.
- **Grounded means grounded.** A signal marked grounded must carry a quote and an
  attribution, and a whitespace-only quote is rejected, so an inference cannot be
  dressed up as evidence.
- **The deck cannot drift from its preview.** A slide is authored once and
  rendered to both the PPTX and the SVG preview from identical coordinates. A
  test asserts every shape's bounding box matches in both.
- **The slides are checked before they render.** Off-canvas geometry, `NaN`
  coordinates from an arithmetic typo, malformed colours, em dashes, and text
  contrast below the WCAG threshold for its size. That contrast rule exists
  because black-on-near-black text once shipped from this codebase, invisible to
  every other gate.
- **Google Slides compatibility is verified, not assumed.** The generated `.pptx`
  is unzipped and scanned for line connectors and dashed lines, which Slides
  silently drops on import.

## Requirements

- **Python 3.9 or newer.** Standard library only, no `pip install`.
- **Node 18 or newer.** Only `create-slides` needs it, and only for `pptxgenjs`.
- **Optional: LibreOffice and poppler**, for the visual-QA loop that renders the
  deck to images so you can look at every slide. Without them the deck still
  builds and is still checked mechanically, but the skill prints
  `VISUAL QA SKIPPED - SLIDES UNVERIFIED` and will not claim a visual pass it did
  not perform.

## Developing on it

Symlink the skills instead of installing the plugin, so your edits are live:

```bash
for s in demo-studio demo-discovery build-spec deck-flow-guide create-slides presenter-guide; do
  ln -s "$PWD/demo-studio/skills/$s" ~/.claude/skills/$s
done
```

Do not do both at once, or every skill loads twice.

Run the tests:

```bash
cd demo-studio
python3 -m unittest discover -s tests    # on 3.9 and on 3.12
node --test                              # from demo-studio/, no path argument
bash tests/test_pptx_tools.sh
```

The two HTML generators are pinned by golden files in `tests/baseline/`. If a
change alters them, that is a real change to shipped output and wants looking at
rather than re-baselining.

## How it is put together

```
demo-studio/
  shared/          brand tokens, guardrails, config validation, traces, pptx probe
  skills/          the router and five workers, each with its own references and assets
  tests/           118 Python, 49 node, one shell suite
docs/superpowers/  the design spec, the implementation plan, and the decision record
```

`docs/superpowers/decisions/` records every ruling taken while building this,
including where the implementation knowingly diverged from its own spec, and the
follow-ups that are still open. It is candid on purpose.

## Credit

The original single skill was written by a colleague and shared through Claude
Desktop. This repository restructured it into a plugin and made its stated
disciplines enforceable. The generators, the format, and the brand system are
substantially their work.
