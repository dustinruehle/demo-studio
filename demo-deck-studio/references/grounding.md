# Grounding, provenance, accuracy

The load-bearing discipline. Everything customer-facing must trace to a source, and
designed choices must be labeled as such.

## Grounded vs inferred

When you propose a demo domain, a scenario, or a talking point, split it:

- **Grounded** — the customer said it. Quote or attribute it.
- **Inferred** — you designed it to exercise their stated needs. Say so plainly.

When the user asks "did they actually say that?", answer with a small table:
element | what the call contains | grounded or inferred. Do not smuggle inferences
in as facts.

## Traces-to

Every flow-guide card and every scripted talking point should trace back to a
discovery signal (an attributed quote) or to a specific demo beat. If it can't be
traced, it probably doesn't belong.

## Reference wins (for build specs and technical claims)

- Verify SDK/API names, version floors, doc URLs, and feature status against the
  authoritative reference (product docs, the SDK reference files, the samples) —
  not memory.
- In the build spec, state explicitly that the skill reference files and pattern
  pages OVERRIDE anything in the spec or in sample code. Mark anything you couldn't
  verify as "verify against <reference>" rather than asserting it.
- Pin pre-release/experimental versions and flag them; when two pre-release pieces
  share a runtime, the higher floor governs.

## Public-safe

If a repo or artifact may go public: no customer names, no participant names, no
internal hostnames/URLs, no real credentials. Ship a curated grep gate
(word-bounded, case-insensitive) over the distinctive identifiers, and eyeball the
false-positive-prone ones. A synthetic domain skin (e.g. a made-up healthcare or
warranty dataset) is fine; a customer's name is not.

## No AI-tells

Trim filler ("seamless", "robust", "leverage", "genuinely", "delve", "honestly",
"actually"). No em dashes anywhere — commas or restructure. Engineer-to-engineer
register: terse, direct, commit to a recommendation rather than hedge.
