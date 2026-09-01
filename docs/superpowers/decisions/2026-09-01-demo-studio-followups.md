# Demo Studio plugin: follow-up backlog

Findings deliberately deferred during execution, plus the two recommendations
the final review promoted. Nothing here blocks merge; the top two are the ones
worth doing soon.

## Do these first

### 1. The low-contrast lint rule is mis-tiered in both directions

`skills/create-slides/assets/lint_slides.js`. It gates box body text at the WCAG
normal-text ratio of 4.5:1, but those runs carry no explicit size and render at the
18pt default, which is the large-text tier of 3:1. So it rejects the brand's own
accent: indigo on the panel is 4.19:1 and hard-fails the build, with no per-op
escape. Meanwhile it skips `label` ops entirely, and at 9pt those are the only
text genuinely in the normal tier. Strict where it should be lenient, silent where
it should be strict. Nothing in the repo trips it today: the shipped eyebrow passes
at 4.69:1, 4 percent of headroom.

### 2. The guardrail meta-key skip is depth-unbounded

`shared/guardrails.py`. `if key in _META_KEYS: continue` fires at any nesting
depth, so a subtree under a nested key named `banned_terms` or `allow_words`
escapes the em-dash, AI-tell and public-safe checks alike. One-line fix:
`if not _path and key in _META_KEYS`. It is a hole in the gate the final fix
wave existed to repair, and the docs now overclaim by saying the scan covers
every text field.

## Also open

- The low-contrast rule is documented nowhere. An author who hits it has no reference.
- A missing or unparsable primary config still raises a raw traceback in all three
  generators, against spec V4. `traces.load_discovery` already has the pattern to copy.
- An unparseable colour silently passes every lint rule and then renders wrong.
- Act colours now live only as prose in `presenter-guide-format.md`, which is the
  state spec section 3 named as the problem. A knowing trade, recorded in the rulings.
- `shared/traces.py` cites a review-finding id in a comment, meaningless to a reader.
- Plugin installation is undecided and undocumented: local marketplace entry, or
  symlink the skills into ~/.claude/skills. Spec section 11 flagged this as needing
  an answer before the skills are usable outside this repo. It still needs one.

## Deferred minors, none blocking

- Task 3: minor (deferred): `DEMO_STUDIO_PROBE_ONLY` is set by tests/test_pptx_tools.sh case 3 but never
- Task 3: minor (deferred): render_preflight invokes check_render_tools twice (test, then capture).
- Task 4: minor (deferred): demo-discovery stub description is more built out than the other four stubs.
- Task 4: minor (deferred): pipeline.md's "FINAL aggregate deck" qualifier not restated in
- Task 4: minor (deferred): create-slides quickstart had one comment split onto its own line, slightly
- Task 5: minor (deferred): brand.load() returns the live module cache and FONTS binds the live nested
- Task 6: minor (deferred): allow_words containing JSON null raises AttributeError. Task 8's schema types
- Task 7: minor (deferred): sorted() puts slide10 before slide2 in report ordering for 10+ slide decks.
- Task 7: minor (deferred): regexes miss self-closing <p:cxnSp/> and single-quoted prst='...'; the
- Task 7: minor (deferred): the try block wraps the detection loop as well as the file open, so a
- Task 11: minor (deferred): negative width caught but labelled zero-size rather than invalid-size.
- Task 11: minor (deferred): box.opts.color not covered by hash-in-hex (slidekit strips the hash anyway).
- Task 11: minor (deferred): guardrails.py keeps a literal em dash with a test exemption while
- Task 11: minor (deferred): require('path') vs require('node:path'); missing trailing newline.
- Task 12: minor (deferred): whitespace-only `text` on a signal, or a whitespace-only `engagement`, still
- Task 14: minor (deferred): router entry-table multi-step row lists workers in prose rather than
