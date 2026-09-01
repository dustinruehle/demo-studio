# Build spec: <Demo name>

**Audience:** the coding agent that will build this.
**Goal:** <one paragraph: the durable business process (outer harness) orchestrating
<N> framework agents (inner harness), what it proves, and the two-lane dashboard>.

Generic and public-repo-safe (see §Generic). Default posture: mock models, local
dev server, no keys.

## 0. How to work (order of operations)
1. Preflight (§Preflight): install/verify prerequisites at the right versions FIRST.
2. Load the skills and read the reference files (§Skills). Reference wins.
3. Scaffold; implement the happy path; write its test; green before proceeding.
4. For each beat (§Beats), in order: implement, test, run until green.
5. Dashboard, scripts, docs.
6. Run the definition-of-done gate (§DoD). Iterate until every item passes.
7. Run the generic sweep (§Generic).
Do not declare done until the whole gate is green.

## 1. Skills to use (reference wins)
- <skill/reference #1: read before X>
- <skill/reference #2: read before Y>
State: if any API here differs from the reference, THE REFERENCE WINS. Mark
anything unverified as "verify against <reference>".

## 2. Reference repositories (structure and idiom)
- <repo/path>: <what to mine, which beats>
Caveat: read for structure; API specifics come from §1, not the samples.

## 3. What it proves (throughline)
<the one durable workflow, the <N> agents, the human gate, the mock-stubs-model
principle: durability/visibility are real in mock mode>.

## 4. Tech + repo layout
<language, package manager, SDK + version floor, test runner, dashboard stack,
lint/type, entry points, task queues, repo tree>.

## 3a/Preflight
Install/verify <toolchain> on <OS>; idempotent; echo privileged/pipe-to-shell
commands first; print a version table; verify pre-release imports; note one-time
downloads. Exit non-zero if unsatisfiable.

## 5. The beats (each runnable three ways: dashboard button, beat runner, manual)
- Beat 1: happy path: <patterns/refs>: <proves>
- Beat 2: durability / money moment (kill a worker): <proves>
- Beat 3: <onboarding / framework-native>: <proves>
- Beat 4: retry vs fail-fast: <proves>
- Beat 5: human gate + saga: <proves>
- Beat 6: composition + history (talk + show)

## 6. Domain model
<neutral vocabulary; only a reference id crosses task queues; mock/real per
component by env; scenario profiles that drive deterministic on-stage behavior>.

## 7. Dashboard (dumb, two-lane)
PLATFORM lane = server-side truth (survives worker death). WORKER lane = live query
(goes OFFLINE, dims the pipeline). No business logic in the dashboard.

## 8. Definition of done (build until ALL pass)
0. preflight OK. 1. deps clean. 2. typecheck. 3. lint. 4. tests pass (no net/keys),
including a self-contained replay test. 5. run script boots everything. 6. each beat
runs three ways. 7. money moment verified. 8. mock<->real by config only. 9.
local<->cloud by config only. 10. generic sweep passes.

## 9. Generic / public-safe
Neutral code vocabulary; swappable domain skin; `check-generic` grep gate (word-
bounded) over customer/participant identifiers; no real names/hosts/creds.

## 10. Docs to produce
README, RUNBOOK (presenter script + switches), CUE_CARD, BUILD_SUMMARY (versions
pinned, references used per beat, deviations).
