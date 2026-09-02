# Build spec

A spec a coding agent (e.g. Claude Code) can execute end to end to build the demo.
Template skeleton: `assets/build_spec_template.md`.

## Non-negotiables (the parts that made the real one hold up)

1. **Order of operations up front.** A numbered loop the agent follows, ending in a
   definition-of-done gate. Say "do not declare done until the gate is green."

2. **Name the skills and reference files to read, and enforce reference-wins.**
   List the exact references (SDK reference files, integration docs, pattern pages)
   and state that they OVERRIDE anything in the spec or in sample code. Mark
   anything unverified as "verify against <reference>".

3. **Reference repositories.** Pin the canonical sample repos to mine for structure
   and idiom, with the caveat that public samples drift, so API specifics come from
   the reference, not the sample.

4. **Preflight that installs prereqs on a fresh machine.** Detect and install the
   toolchain (idempotent, echo privileged/pipe-to-shell commands first, print a
   version table). Verify pre-release integration imports explicitly, since a
   missing extra is the most likely first-run failure. Note the target OS.

5. **Definition-of-done gate with tests that loop until green.** Enumerate the
   required tests; instruct "iterate test -> implement -> run -> fix until ALL
   pass." Include a self-contained replay test. Tests need no network/keys.

6. **Mock-by-default switch.** Stub the model, never the integration, so durability
   and behavior are real with no keys. A per-component real toggle by env only. And
   local-vs-cloud by env only.

7. **Generic / public-safe.** Neutral code vocabulary; a swappable domain skin;
   a `check-generic` grep gate wired into the DoD. No customer/participant names.

8. **Version pinning.** Pin exact versions of pre-release pieces; when two share a
   runtime, the higher floor governs. Flag pre-release status in the README.

## Structure that worked

Order-of-operations · Skills-to-use (with reference-wins) · Reference repos ·
Throughline (what it proves) · Tech + repo layout · Preflight · The beats (each
runnable three ways: dashboard button, a beat runner, and manually) · Domain model
· Dashboard (a *dumb* two-lane reader: a server-side lane that survives crashes and
a worker-query lane that goes offline) · Scripts · Cue card · Definition-of-done
gate · Generic/public requirements · Docs to produce · Appendices (cue-card
template, pattern->slug map, verified version pins).

The **two-lane dashboard** is the demo's proof device: one lane from durable
server-side state (survives a worker dying), one from a live worker query (goes
OFFLINE and dims the pipeline). Kill a worker, watch the split. Keep it dumb: no
business logic in the dashboard.
