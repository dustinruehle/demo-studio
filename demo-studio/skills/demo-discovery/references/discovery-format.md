# Discovery format

Produced by `assets/build_discovery.py CONFIG.json OUT.md`. The JSON is the
durable artifact; the Markdown is the version a human reads. See
`assets/examples/discovery.example.json`.

## What it is

A record of the signals pulled from a discovery call, mapped to demo fit and
a session design. Later pipeline stages, the flow guide and the presenter
guide, reference this record by signal id instead of restating the call from
memory. This is what makes "everything traces back to discovery" a build
check instead of an honour system: a `traces` field that names a signal id
that does not exist here is a build failure, not a review comment.

## Config fields

Top level: `engagement` (a short label, no customer name), `signals` (list,
required), `demo_fit` (list), `session` (object), `fork` (object).

**signal:** `id`, `kind` (`"grounded"` or `"inferred"`), `text` (required).
A grounded signal also requires `quote` and `attribution`. An inferred signal
may list `exercises`, the ids of the grounded signals it was designed to
answer.

**demo_fit row:** `demo`, `why`, `verdict` (`"lead"`, `"second"`, or
`"skip"`).

**session:** free-form, but `pitch` (boolean), `deployment`, and `beats`
(list of `[start, name, minutes]`) are what the render expects.

**fork:** `choice` (`"v1"` or `"v2"`) and `why`, the one-line reason for
picking one over a fused build.

## The `D\d+` id convention

Signal ids are `D1`, `D2`, `D3`, in the order they surfaced. The accepted
shape is `^D[1-9]\d*$`: no leading zeros. `D1` and `D01` would otherwise be
two different strings naming the same intended signal, and the flow-guide and
presenter-guide generators extract ids from free prose with `\bD\d+\b`, so a
stray leading zero would silently fail to match rather than being flagged as
a typo. Do not renumber an id once other files reference it; append instead.
`exercises` and every downstream `traces` field point at these ids, so an id
is load-bearing the moment it ships, not just a label.

## Grounded versus inferred

This is the same split documented in `../../../shared/grounding.md`, made
mechanical here:

- **Grounded**: the customer said it. Carries `quote` (verbatim) and
  `attribution` (a role, such as "platform lead", never a name). Missing
  either one is a build error, because an unattributed quote is not
  provenance, it is a claim wearing provenance's clothes.
- **Inferred**: a choice the team designed, not something said on the call.
  No quote to invent. Use `exercises` to say which grounded signals it was
  built to answer, so a reviewer can see the design followed the evidence.

## Traces-to, for later stages

The `traces` field on flow-guide cards and presenter-guide talking points
resolves against the ids defined here. A card that traces to `D2` is
asserting that discovery signal exists and says what the card claims it says.
A card that traces to an id this file never defines fails the build, naming
the card and the missing id. A card that traces to nothing at all (free text,
no `D` number) only warns, so an engagement's existing cards keep building
while discovery adoption is gradual; it does not fail the build.

## Public-safe

`attribution` is a role, never a name. `engagement` is a label, never a
customer name. `quote` may be verbatim, but only the part that describes the
problem, never anything that identifies who said it beyond the role. If a
call surfaced a real company name, a real person's name, or an internal
hostname, it does not belong in this file at all, paraphrase around it.

### `allow_words` and `banned_terms`

Optional top-level fields, both arrays of strings, read by the same guardrail
that scans every text field in this config:

- `banned_terms`: identifiers that must never reach the output (a real
  customer name, a codename, an internal host). Any match anywhere in the
  config, case-insensitive and word-bounded, hard-fails the build.
- `allow_words`: a documented escape for the AI-tell filter. If a listed word
  ("robust", "actually", etc.) is doing legitimate technical work here, name it
  in this list rather than rewording around a false positive.
