# Demo Studio plugin: follow-up backlog

Findings deliberately deferred during execution, plus the two recommendations
the final review promoted. Nothing here blocks merge; the top two are the ones
worth doing soon.

## Done

- **The low-contrast rule's tiering, fixed.** It now derives the WCAG threshold
  from the text's actual rendered size: 3:1 for large text (18pt, or 14pt bold
  and above), 4.5:1 otherwise. Box runs carry no explicit size and render at the
  pptxgenjs 18pt default, so they take the large tier and the brand accent passes
  at 4.19:1. Labels are 9pt and take the strict tier, so they are now checked at
  all, which they previously were not. Both directions are pinned by tests that
  were watched failing first.
- **The guardrail meta-key skip, scoped.** `banned_terms` and `allow_words` are
  exempt only at the top level, where they are the config's own meta fields. A
  nested key that merely shares the name is ordinary content and is scanned again.
- **Plugin installation, decided.** The repo ships a marketplace manifest and is
  installable with two commands; the router names workers without a namespace
  prefix so it reads correctly under both install methods.

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
