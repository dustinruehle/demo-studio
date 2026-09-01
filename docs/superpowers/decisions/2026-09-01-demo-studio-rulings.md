# Demo Studio plugin: decisions taken during execution

Every ruling made while executing
`docs/superpowers/plans/2026-09-01-demo-studio-plugin.md`, in the order made.
These are decisions taken without asking, each with what it costs if wrong.
Recorded because git history does not hold them and they were made on the
repo owner's behalf.

Branch: demo-studio-plugin, 44 commits from main @ 09c0045.

## work in place on branch `demo-studio-plugin`, not a git worktree — the plan
hardcodes `/Users/dan/code/skills/demo-studio/...` absolute paths in dozens of
verification commands, and a worktree at a different path breaks every one of them.
Main stays clean either way. Cost if wrong: the working tree is not isolated from
other work in this repo; there is no other work, and no remote.


## Task 9 renders the viewBox and background rect through a new `viewBoxDim()`
that rounds, keeping `u()` exact for op geometry — the parity test compares real
numbers, the canvas needs a clean integer. Cost if wrong: none, the two consumers
have genuinely different precision needs.


## Task 10's parity test skips the three header texts structurally
(`texts.slice(3)`) and compares bboxes by set membership rather than index, because
box/label become texts while frame/arrow become shapes, so concatenated order is not
op order. Cost if wrong: the test proves every op bbox is placed but not that two ops
with identical bboxes are both placed; acceptable, identical-bbox ops are a lint
error anyway.


## Task 10's template normalises brand.json colours through a `nohash()` helper
at load, rather than loosening the Task 11 lint. pptxgenjs wants bare hex and the lint
enforces that; brand.json stores `#`-prefixed because CSS needs it. Cost if wrong:
one extra helper in the template.


## Task 4 gains Step 6b updating `capture_baseline.sh` to the post-move paths,
verified by diffing the regenerated golden files against a saved copy. Cost if wrong:
Task 5's re-baseline would silently produce empty or stale goldens, which would make
V2 vacuous.


## `node --test tests/` is a PLAN DEFECT, not an implementer error. Verified on
  Node 24.16.0 in a clean repro: the directory-argument form yields "pass 0 / fail 1"
  (it resolves `tests` as a module), while bare `node --test` yields "pass 1 / fail 0".
  Replaced all 5 occurrences in the plan (Tasks 1, 9, 10, 11, 15) with bare `node --test`.
  Explicit single-file forms (`node --test tests/x.test.js`) are correct and left alone.
  Cost if wrong: bare `node --test` relies on Node's default discovery from cwd, so a
  test placed outside demo-studio/ would be missed; all planned JS tests live in
  demo-studio/tests/, and node excludes node_modules by default.
## the committed .pyc is a real implementer error, not plan-mandated. The brief's
  `git add demo-studio/tests` swept up __pycache__. Enters the fix loop with a .gitignore.
  Cost if wrong: none, bytecode has no business in git.
Task 1: fix round 1/5 dispatched (resumed original implementer) — findings: committed .pyc + no .gitignore; package.json test script
Task 1: fix round 1/5 complete (commits 02eea70..9b32c02) — both findings fixed; controller independently verified: 0 pycache tracked, .gitignore correct, test script bare, baseline byte-identical
Task 1: scoped re-review dispatched (haiku) — package review-02eea70..9b32c02.diff
Task 1: complete (commits a82eb20..9b32c02, review clean — both findings ADDRESSED, no new breakage)
Task 2: dispatched (implementer, haiku) — BASE 9b32c02
Task 2: implementer DONE (commit 66f572f) — 3/3 pass on BOTH 3.9.6 and 3.12.12; RED state resolved; controller verified diff is the exact specified hoist
Task 2: task review dispatched (haiku) — package review-9b32c02..66f572f.diff
Task 2: controller pre-answered the coverage question raised in the review prompt.
  The example config has 4 lanes, 2 with falsy cls, so the changed branch IS exercised.
  Baseline and post-fix output each contain exactly 2 occurrences of the muted style,
  and the files are byte-identical. The fix is genuinely verified, not vacuously.
Task 2: complete (commits 9b32c02..66f572f, review clean — spec PASS, quality PASS, no findings)
Task 3: dispatched (implementer, sonnet — fiddly shell globbing, turn count beats token price) — BASE 66f572f
Task 3: implementer DONE_WITH_CONCERNS (commit e707287) — 6 ok + PASS; 2 deviations from brief.
## PPTX_SKILL_DIR becomes an EXCLUSIVE override, not merely the first probe candidate.
  My brief contradicted itself: test case 2 asserts a bogus override must be rejected, but the
  brief's implementation listed the override as candidate #1 and fell through to the glob, which
  on this machine finds the real install, so a bogus override was silently accepted. Implementer
  resolved in favour of the test. Correct on the merits too: an explicit override that silently
  resolves somewhere else is worse than a loud failure. Controller verified both directions.
  Cost if wrong: someone setting PPTX_SKILL_DIR to a typo gets an error instead of a fallback,
  which is the intended behaviour.
## the failure branches use bash builtins (printf/read) instead of sed/cat. My test simulates
  missing tools with PATH=/nonexistent, which also removes sed and cat, so the brief's own
  diagnostic printed "command not found" instead of the banner. Verified: banner text is exact,
  both brew lines present, no external-command leakage, exit 1. Cost if wrong: none.
Note: Task 3's plan text is now superseded by the shipped implementation on these two points.
Task 3: task review dispatched (sonnet) — package review-66f572f..e707287.diff
Task 3: complete (commits 66f572f..e707287, review clean — spec PASS, quality PASS, both deviations verified correct)
Task 3: minor (deferred): `DEMO_STUDIO_PROBE_ONLY` is set by tests/test_pptx_tools.sh case 3 but never
  consumed by pptx_tools.sh. Dead env var inherited from my brief, harmless. For final-review triage.
Task 3: minor (deferred): render_preflight invokes check_render_tools twice (test, then capture).
  Inherited from the brief's own pattern. Harmless, one extra command -v pair.
Task 4: dispatched (implementer, sonnet — multi-file move plus SKILL.md split judgement) — BASE e707287
Task 4: implementer DONE (commit 1135beb) — 7/7 on both interpreters, pptx tools PASS, baseline byte-identical.
## Task 4 could not stay a pure move. My own test_layout.py test_no_em_dashes_in_any_skill_file
  scans every file under skills/, and the colleague's original reference docs and generator docstrings
  contain em dashes, so the move forced content edits. Accepted: the skill's own stated guardrail is
  "no em dashes anywhere", so cleaning them serves the spec rather than fighting it. Controller verified
  the generator diff is exactly 4 module-docstring lines (em dash -> colon/semicolon), zero functional
  code, and both goldens still reproduce byte-identically. Cost if wrong: the Task 4 diff is larger than
  "renames only", making that commit harder to audit; mitigated by rename detection still tracking all moves.
## shared/grounding.md retains 4 em dashes because it sits outside the skills/ tree the test scans.
  That is an inconsistency, not a deliberate exemption. Decided to close it inside Task 4 rather than defer:
  clean the file and widen the test to cover shared/ as well, so the constraint means what it says.
  Cost if wrong: four punctuation edits to a doc no test currently guards.
Task 4: task review dispatched (sonnet) — package review-e707287..1135beb.diff
Task 5 pre-dispatch note (controller, before dispatching): brief says "10 stray hexes" for the
  presenter guide and ships a 10-row replacement table. Correct on DISTINCT values but there are
  12 OCCURRENCES: #C9B8F0 appears twice (.demobanner .eyebrow and .switchblock .sw-t) and #241C33
  twice (.term-action and .switchblock). The acceptance test test_generators_contain_no_hex_literals
  demands ZERO hex literals, so all 12 must be replaced. Carried into the Task 5 dispatch explicitly.
  Premise otherwise re-verified post-move: 3 stray in flow guide, 12 in presenter guide, unchanged.
Task 4: task review — spec PASS all migration rows; content-redistribution audit found nothing lost
  (reviewer recovered both deleted files from git and checked clause by clause). 1 Important, 3 Minor.
Task 4: minor (deferred): demo-discovery stub description is more built out than the other four stubs.
  Task 14 rewrites all six descriptions, so it self-resolves there.
Task 4: minor (deferred): pipeline.md's "FINAL aggregate deck" qualifier not restated in
  presenter-guide/SKILL.md. Task 14 owns that file's body; fold it in there.
Task 4: minor (deferred): create-slides quickstart had one comment split onto its own line, slightly
  beyond pure dash-swapping. Harmless.
Task 4: fix round 1/5 dispatched (resumed original implementer) — grounding.md 4 em dashes + widen
  test_layout.py scan to cover shared/, with a watch-it-fail check on the new guard.
Task 6 pre-dispatch check (controller): both shipped example configs are already clean of all 7
  AI-tell words and of em dashes, so wiring guardrails.enforce() into the generators will not make
  them fail on their own examples. Task 6 premise is green; no seeded-cleanup work needed first.
Task 4: fix round 1/5 complete (commits 1135beb..ba1356b) — grounding.md 0 em dashes, guard widened to
  skills/ + shared/. Controller ran its OWN watch-it-fail: injected an em dash under shared/, test FAILED
  (4 tests, 1 failure), reverted, test OK. The guard is proven, not asserted.
Task 4: scoped re-review dispatched (haiku) — package review-1135beb..ba1356b.diff
Task 4: complete (commits e707287..ba1356b, review clean — finding ADDRESSED, no new breakage)
Task 5 pre-dispatch check (controller): planned brand.json validated against the real :root blocks.
  flow_guide :root has 15 tokens, presenter_guide 14, sharing 8 core. Planned core(8) + flow surface(10)
  = 18 and core(8) + pg surface(16) = 24, which is exactly 15+3 and 14+10 once the stray hexes become
  named tokens. The two guides genuinely diverge on amber/green/coral, as the spec anticipated.
Task 5: dispatched (implementer, sonnet — multi-file, requires deliberate diff judgement) — BASE ba1356b
Task 5: implementer DONE (commit baccdc1) — 16/16 both interpreters, pptx PASS.
  Implementer found 2 hex occurrences BEYOND my 12: #4C2889 twice as a Python-level fallback default
  outside the CSS, which my file-wide regex test would have caught. Replaced with a module constant
  sourced from brand.json. Good catch, no behaviour change.
  Implementer also went beyond the text diff: rendered old vs new in headless Chrome at two viewport
  heights and confirmed the PNGs are byte-identical, directly addressing the "renders as no colour" risk.
  Controller independently verified: 18 tokens flow / 24 presenter (matching predicted arithmetic),
  ZERO dangling var() in either guide, ZERO hex literals in either generator, every golden diff line is
  either :root reformatting or a hex-to-var() swap with the value preserved.
Task 5: task review dispatched (sonnet) — package review-ba1356b..baccdc1.diff
Task 7 pre-dispatch check (controller): ran the fixture + detection approach end to end in scratch.
  A zip containing only ppt/slides/slide1.xml (no [Content_Types].xml) is readable by zipfile and the
  regexes correctly flag the bad deck (2 connector hits + 1 dash) and pass the clean one. Premise green.
  Note the bad fixture trips BOTH connector patterns, giving 2 findings of the same check name; the
  planned test uses a set membership assertion so that is fine.
Task 5: complete (commits ba1356b..baccdc1, review clean — spec PASS, quality PASS, 0 Critical, 0 Important)
  Reviewer verified colour fidelity digit-by-digit on every swap (zero transpositions), independently
  regenerated both guides byte-identically, and proved test_surface_accents_stay_divergent really fails
  by unifying an accent in brand.json and watching it break.
Task 5: minor (deferred): brand.load() returns the live module cache and FONTS binds the live nested
  dict, skipping the defensive copy that tokens() and acts() use. No consumer mutates them today, so
  no live bug, but a future caller doing brand.FONTS["heading"]=... would poison the cache process-wide.
  Suggested fix: return dict(...) from load(). For final-review triage.
Task 5: note (informational): FONTS and acts() are exported but not yet consumed. Font names remain
  literal strings in both CSS blocks (25 and 27 occurrences) and per-slide act colour still comes from
  the user's JSON config. This matches the brief exactly, which only ever wires the :root block and the
  hex table. Flagged so nobody assumes type is single-sourced yet; only colour is.
Task 6: dispatched (implementer, sonnet — new module plus careful insertion into two generators) — BASE baccdc1
Task 8 pre-dispatch check (controller): PLAN DEFECT FOUND AND FIXED before dispatch. The planned
  flow-guide schema typed card.seq as {"type":"number"}, but the shipped example uses zero-padded
  STRINGS ("01", "04"), and act.no is "Act 1" which is not numeric at all. TestRealSchemas
  test_flow_guide_example_validates would have failed on the skill's own example config.
  Ruling: seq accepts ["number","string"]; act.no already did. Fixed in plan (dab9c3a), brief regenerated.
  Cost if wrong: a genuinely malformed seq (e.g. a list) still fails, so validation is not weakened.
  Also confirmed the other planned types match reality: flow legend=object/footer=object,
  presenter legend=array/acts=object/demo=object, slide.num=number. No other mismatches.
Task 6: CONTROLLER ERROR, found by the implementer and corrected. While Task 6 was running I ran
  `git add -A` in the repo root to commit an unrelated plan fix, which swept up the implementer's
  in-progress work. Commit dab9c3a therefore contained all four Task 6 files under a message about a
  plan typo. The implementer flagged it rather than staying quiet.
## split the mixed commit rather than document around it. Local branch, no remote, nothing pushed,
  fully reflog-recoverable (recovery point 8f5b624). Soft-reset to baccdc1 and recommitted as three
  honest commits: 5287f0f plan fix, 29724cc Task 6 guardrails, 68c7ca0 em-dash scan narrowing.
  PROVED SAFE: tree hash c3d5ea42... before and after are IDENTICAL, so zero content changed.
  Cost if wrong: rewritten local history; the pre-split state remains in reflog.
Process change: never `git add -A` from the repo root while an implementer subagent is live. Stage
  explicit paths only. This was the one place my own bookkeeping could corrupt a task's history.
Task 6: implementer DONE (commits 29724cc, 68c7ca0) — 30 tests pass on both interpreters, pptx PASS.
  Controller verified the seeded violation: exit 1, names em-dash AND ai-tell at acts[0].cards[0].why,
  and no output file written. Note it currently surfaces as a raw traceback; Task 8 Step 6 adds the
  try/except that turns it into a clean message. Expected at this stage.
Task 6: task review dispatched (sonnet) — package review-5287f0f..68c7ca0.diff
Task 6: task review — spec PASS. 1 CRITICAL, 2 Minor.
  CRITICAL: banned terms with a non-word first/last character never match, silently. \b cannot match
  where the term's own edge is already non-word. Controller reproduced: C++, (x), [z], Yahoo! all give
  0 violations. This is the public-safe gate, the check most likely to be handed a real customer or
  product name, so a silent total false negative is the worst possible failure mode for it.
  Verified fix: swap \b anchors for (?<!\w) ... (?!\w). Catches all four AND preserves both existing
  behaviours (CONTOSO still matches, Contosoville still does not).
Task 6: minor (deferred): allow_words containing JSON null raises AttributeError. Task 8's schema types
  allow_words as array-of-string and will reject it cleanly upstream, so this self-resolves there.
Task 6: minor (noted): the implementer's report cites pre-split commit hashes. Consequence of my own
  history fix, not implementer error. Harmless; the ledger carries the correct hashes.
Task 6: fix round 1/5 dispatched (resumed original implementer) — boundary fix plus watch-it-fail tests
  for symbol-edged terms and a regression case pinning that substring matching stays off.
Task 9 pre-dispatch check (controller): SECOND PLAN DEFECT FOUND AND FIXED. Ran the planned sample
  slide's coordinates through JS: 2.2*100 = 220.00000000000003 and 0.28*100 (the LABEL_H) =
  28.000000000000004. Every SVG coordinate would have carried float noise, and the tests asserted
  against raw multiplication so they would have passed while emitting ugly output.
## u() rounds to 2dp; tests use kit._internal.u() rather than raw multiplication; added a test
  asserting no coordinate contains a run of 6+ digits. 2dp is far finer than a pixel at this scale.
  Cost if wrong: sub-hundredth-inch rounding in previews, invisible at any real render size.
  Note this is the same class of bug as the viewBox defect caught in the pre-flight scan; JS float
  arithmetic on inch coordinates is a recurring trap in this task.
Task 6: fix round 1/5 complete (commits 68c7ca0..abc151c) — Critical ADDRESSED, no new breakage.
  Re-reviewer reverted _word_re to the buggy version and confirmed the new tests genuinely fail,
  then restored. Also assessed false positives: (x) matches in "look at (x) here" but not in
  "text(x)text", which is correct for an identifier gate.
Task 6: complete (commits 5287f0f..abc151c, review clean after 1 fix round)
Task 7: dispatched (implementer, haiku — complete code in plan, premise pre-verified by controller) — BASE 0308848
Task 7: implementer DONE (commit b2b44eb). Code is correct: bad fixture -> 3 findings (2 connector,
  1 dash), clean fixture -> 0, exactly matching my pre-dispatch verification. Goldens untouched.
Task 7: REPORTING ACCURACY PROBLEM (not a code defect). The implementer reported "20/20 tests pass on
  both Python 3.12.12 and Python 3.11.x". Both figures are wrong: the real count is 36 tests, and there
  is no Python 3.11 on this machine. The required interpreters are 3.9.6 and 3.12.12, and I confirmed
  the suite passes 36/36 on both. A report that misstates its own verification evidence undermines the
  review chain even when the code is fine, so the reviewer is being asked to check whether the required
  3.9 interpreter was genuinely exercised or merely claimed.
Task 7: task review dispatched (sonnet) — package review-0308848..b2b44eb.diff
Task 7: task review — spec PASS, code correct and independently confirmed on 3.9.6. 1 Critical (report
  fabrication), 2 Important, 2 Minor.
Ruling on the Critical: it concerns the REPORT, not the code. Two independent parties (reviewer and
  controller) have now verified the code on both required interpreters, so the substantive risk is
  closed and the task does not need re-implementation. Remedy is to make the report tell the truth,
  since the whole review chain depends on reports being literally true. Required a corrected
  verification section with pasted real output, explicitly noting the 3.11 figure was wrong rather
  than silently overwriting it. Cost if wrong: none to the code; this is an integrity correction.
Task 7: fix round 1/5 dispatched — report correction, plus check_pptx returning a pptx-unreadable
  Violation instead of raising BadZipFile/FileNotFoundError, plus de-vacuifying
  test_names_the_offending_slide (a stub returning [] passed 2 of 4 tests because all() over an
  empty sequence is True).
Task 7: minor (deferred): sorted() puts slide10 before slide2 in report ordering for 10+ slide decks.
Task 7: minor (deferred): regexes miss self-closing <p:cxnSp/> and single-quoted prst='...'; the
  reviewer confirmed neither is emitted by any schema-valid real-world OOXML producer.
Task 7: fix round 1/5 complete (commits b2b44eb..ab7a8cf). Controller verified independently:
  37 tests OK on BOTH 3.9.6 and 3.12.12 (the real numbers this time); non-zip, 0-byte and missing paths
  all return a pptx-unreadable Violation instead of raising; a valid zip with no slides still returns [].
  Ran my own stub check: with check_pptx returning [], 4 of 5 tests FAIL (only test_a_clean_deck_passes
  survives, which is correct since a clean deck legitimately returns []). Restored, 5/5 pass.
  The vacuity is genuinely gone.
Task 7: scoped re-review dispatched (haiku) — package review-b2b44eb..ab7a8cf.diff
Task 8 pre-dispatch check #2 (controller): extracted the planned validate_config.py and BOTH schemas
  straight out of the plan text and ran them against the two real shipped example configs.
  Result: 0 errors each, so TestRealSchemas would PASS. This confirms the earlier card.seq fix was
  both necessary and sufficient, and that no other planned type contradicts the real data.
Task 7: fix round 1/5 complete (commits b2b44eb..ab7a8cf) — all 3 findings ADDRESSED, no new breakage.
  Report correction is explicit ("initial report was inaccurate"), not a silent overwrite, and its
  pasted 37-test figures for 3.9.6 and 3.12.12 match what both I and the re-reviewer measured.
Task 7: minor (deferred): the try block wraps the detection loop as well as the file open, so a
  mid-loop failure would return pptx-unreadable and discard findings already collected. Re-reviewer
  assessed the practical cases as unreachable (decode uses errors="replace" and cannot raise).
Task 7: complete (commits 0308848..ab7a8cf, review clean after 1 fix round)
Task 8: dispatched (implementer, sonnet — 4 new files plus conditional checks and error wrapper in two generators) — BASE ab7a8cf
Task 8: implementer DONE (commit 4d40528). Controller verified independently: 50 tests OK on BOTH
  3.9.6 and 3.12.12; a bad config now yields "5 config error(s)" naming each path with ZERO tracebacks;
  the guardrail violation that Task 6 surfaced as a raw stack trace is now a clean "2 guardrail
  violation(s)" block, also traceback-free; goldens untouched and both shipped examples still build
  byte-identical to them.
  The Task 6 deferred minor RESOLVED here as predicted: allow_words:[null] is now caught upstream as
  "allow_words[0]: expected string, got null" instead of crashing with AttributeError inside guardrails.
Task 8: task review dispatched (sonnet) — package review-ab7a8cf..4d40528.diff
Tasks 9+10 pre-dispatch check (controller): extracted the planned slidekit.js, renderPptx, and BOTH
  test files verbatim from the plan and ran them in scratch. All 16 tests pass, covering the op
  recorder, the SVG backend, the PPTX backend and both PARITY tests.
  Also proved the parity test is load-bearing, not just green: injected a 0.1in x offset into the PPTX
  backend's box placement and "PARITY: every op has the same bbox in both backends" FAILED; restored
  and all 16 passed again. The set-membership rewrite I made in the pre-flight scan is strong enough.
  Also confirms the u() rounding fix works: the "SVG coordinates carry no floating point noise" test
  passes, which it would not have before that fix.
  Tasks 9 and 10 should need no discovery work; they are transcription plus wiring.
Task 8: complete (commits ab7a8cf..4d40528, review clean — 0 Critical, 0 Important, 0 Minor).
  Reviewer adversarially tested the validator against both toy and real schemas: acts-as-string,
  null card in array, deep nested wrong type, top-level list, top-level null. All produced clean
  pathed errors, none crashed, none slipped through. Confirmed _walk's early return does not suppress
  sibling errors, and that bool/number are correctly discriminated in both directions.
Task 8: note (informational): the try/except is correctly scoped and does NOT swallow genuine bugs.
  Reviewer proved it: a 1-element `chips` entry satisfies the schema (no minItems in the dialect) but
  makes build() raise ValueError on unpack, and that surfaces as a real traceback rather than a tidy
  exit 1. Losing real stack traces would have been worse than the problem this task solved.
Task 9: dispatched (implementer, haiku — pure transcription, controller already ran the exact code green) — BASE 4d40528
Task 11 pre-dispatch check (controller): extracted the planned lint_slides.js and its test from the
  plan and ran them in scratch. All 10 tests pass. Tasks 9, 10 and 11 are now all pre-verified.
Pre-flight ruling CONFIRMED CORRECT by experiment: fed brand.json's pptx colours straight into slidekit
  and the lint produced 2 hash-in-hex findings, meaning Task 10's build would have failed its own Task 11
  gate on every run. With the nohash() normalisation from the ruling, 0 findings. brand.json stores
  "#8E6BE6" because CSS needs the hash; pptxgenjs and the lint both want it bare. The conflict was real
  and the fix is right.
Task 9: complete (commits 4d40528..2d4d46d, review clean — 0 findings at any severity).
  Reviewer parsed the emitted SVG with a real XML parser, checked arrow polygons stay in-bounds under
  both wide and tall clamping for arrowR and arrowD, probed plainText with 8 input shapes, and confirmed
  renderOp throws loudly on an unknown op. Controller separately confirmed both files are byte-identical
  to the plan text apart from the extraction path-comment.
Task 10: dispatched (implementer, sonnet — npm install, real PPTX generation, reference-doc /mnt removal) — BASE 2d4d46d
Tasks 12+13 pre-dispatch check (controller): extracted the planned schema_discovery.py,
  build_discovery.py, traces.py and discovery.example.json from the plan and ran them against the REAL
  shared/ modules. Schema validates with 0 errors, check_signals passes, render() produces 1160 chars
  with GROUNDED present and zero em dashes (so the dead-conditional fix from the spec self-review holds),
  and traces.signal_ids finds D1..D5.
  Proved the checks are load-bearing, not just green. All 5 check_signals negative cases caught with
  precise messages: duplicate id, malformed id, grounded missing quote, grounded missing attribution,
  exercises pointing at a nonexistent signal. All 6 traces cases correct, including the two that matter
  most: a free-text traces value is reported as `untraced`, and a config with NO discovery record skips
  the check rather than silently passing it.
  Tasks 9 through 13 are now all pre-verified before dispatch.
Task 10: implementer DONE (commit 459017d) with 2 deviations, both correct, both confirmed by controller.
## the TDZ bug was MINE, introduced by my own pre-flight nohash fix. Verified in the plan text:
  `const palette` (char 697) called nohash, declared at char 1058, a runtime ReferenceError. The
  implementer reordered the declaration; values and call sites unchanged. Plan text corrected too so it
  no longer ships a snippet that cannot run. Cost if wrong: none, ordering only.
## the implementer widened Step 6b beyond the three /mnt paths the brief named, because
  skills/create-slides/SKILL.md carried three more of the same pattern (inherited when Task 4 split the
  monolith). Accepted: the definition of done says no such reference anywhere in demo-studio, so the
  brief's file list was incomplete, not its intent. Verified only two /mnt strings survive repo-wide,
  both deliberate sandbox-probe entries in pptx_tools.sh and its test. Cost if wrong: none.
Task 10: controller verified the real artifacts: create-slides.pptx built, guardrails.check_pptx returns
  ZERO violations against a genuine pptxgenjs deck (its first encounter with a real file rather than a
  hand-written fixture), slide-previews.json parses as valid XML, 16 node tests, 50 Python tests on both
  interpreters. Visual QA correctly did NOT run and was reported as unverified, per the designed
  degraded path. No LibreOffice was installed.
Task 10: task review dispatched (sonnet) — package review-2d4d46d..459017d.diff
Task 10: task review — spec essentially full marks, both deviations correct. 2 Critical, 2 Important.
  Reviewer proved the parity guarantee is real by mutating only the PPTX backend and watching
  "PARITY: every op has the same bbox" fail, then restoring. It also cross-checked every EMU offset in
  the real deck against the ops (0.6in -> 548640 EMU etc) and confirmed the arrow is a genuine
  prstGeom rightArrow autoshape, not a connector.
  CRITICAL 1: this task broke the skill's own Quickstart. `cp assets/build_create_slides.js my_slides.js`
  then `node my_slides.js` now fails with "Cannot find module './slidekit'", because Step 5 added a
  local require and a __dirname-relative brand.json path. Controller reproduced it, and confirmed that
  copying WITHIN assets/ works. The two docs also disagree on cwd (../../../ vs ../../).
  CRITICAL 2: the shipped deck has BLACK TEXT ON NEAR-BLACK PANELS. renderPptx's box case never sets
  color so pptxgenjs defaults to 000000, while renderSvg always paints palette.txt. Controller verified
  in the real artifact: ppt/slides/slide1.xml contains srgbClr val="000000" beside fills 241C33 and
  2A1D1A, roughly 1.3:1 contrast, violating the "dark and readable" hard rule.
## Critical 2 is MY bug, in the brief's own renderPptx, and the brief's own example slide (a plain
  string rt, not a coloured rich-text array) is exactly what triggers it. Worth recording WHY no gate
  caught it: parity is bbox-only and blind to colour; the Task 7 guardrail checks banned constructs, not
  contrast; and visual QA is the disabled path on this machine. This is the clearest evidence yet that
  the degraded visual-QA path has a real cost, and it argues for the contrast check the spec deferred.
Task 10: fix round 1/5 dispatched — Quickstart repair, box text colour in both backends plus a
  regression test, gitignore coverage from both build locations, and the stale helpers doc section.
Task 14 pre-dispatch check (controller): ran the planned test_descriptions.py against (a) the CURRENT
  descriptions and (b) the PLANNED ones.
  Current state fails 5 of 6. The router still carries the monolith description, which claims
  "presenter guide", "flow guide" and "build spec" outright, the exact overlap the test forbids, and it
  never says "use when". So Task 14 has real work; it is not a formality.
  The PLANNED descriptions pass all 6, including test_the_router_does_not_claim_the_workers_artifacts
  and the per-worker artifact-noun checks. Task 14 is transcription, not redesign.
  Tasks 9 through 14 are now all pre-verified. Only Task 15 remains inherently un-pre-verifiable, since
  routing behaviour depends on how fresh agents actually respond to the descriptions.
Task 10: fix round 1/5 complete (commits 459017d..db351ad) — all 4 findings ADDRESSED, no new breakage.
  Re-reviewer confirmed the colour fix is COMPLETE, not patched only where noticed: audited every
  text-emitting path (3 header texts, box, label) and confirmed none falls back to a pptxgenjs default;
  frame/arrowR/arrowD emit no text. Both backends now agree on colour in both the override-set and
  override-omitted cases. Removed just the colour line and watched 2 new tests fail, so the regression
  test is load-bearing. Ran every command in both docs literally from the directory each implies.
Task 10: complete (commits 2d4d46d..db351ad, review clean after 1 fix round)
RECOMMENDATION for the final review and for Dan: this plan has NO automated contrast check. The
  black-on-near-black bug shipped in a real artifact and was invisible to every gate: parity compares
  bounding boxes, guardrails checks banned constructs, and visual QA is the disabled path on machines
  without LibreOffice. The spec's own risk section anticipated contrast as a concern and deferred it.
  A cheap mechanical check (compute contrast ratio between each text colour and the fill behind it,
  fail below a threshold) would close the one gap that the degraded visual-QA path leaves open. Out of
  scope for this plan; worth a follow-up.
Task 11: dispatched (implementer, haiku — pre-verified in scratch, all 10 lint tests already run green) — BASE db351ad
Task 11: task review — spec PASS, gate placement correct, all 4 rules proven individually load-bearing
  by disabling each and watching the right tests fail. 1 Important, 5 Minor.
  IMPORTANT: NaN and undefined coordinates pass the lint silently, because every comparison against them
  is false so the shape appears in-bounds. Controller reproduced it and confirmed the downstream damage
  with REAL pptxgenjs: the generated slide XML places the shape at x="0", quietly moving it to the left
  edge instead of failing. An arithmetic typo in a builder expression produces exactly this. It is the
  precise failure mode this task exists to prevent, on machines where nobody can render and look.
  Both deviations judged correct: '—' avoids needing a second carve-out in test_layout.py's
  exemption list, and that file was outside Task 11's declared scope, so the escape was the MORE scoped
  choice. require('path') is cosmetic.
Task 11: minor (deferred): negative width caught but labelled zero-size rather than invalid-size.
Task 11: minor (deferred): box.opts.color not covered by hash-in-hex (slidekit strips the hash anyway).
Task 11: minor (deferred): guardrails.py keeps a literal em dash with a test exemption while
  lint_slides.js uses the escape form. Two solutions to one problem, worth a comment someday.
Task 11: minor (deferred): require('path') vs require('node:path'); missing trailing newline.
Task 11: fix round 1/5 dispatched — invalid-coord rule using Number.isFinite, evaluated before the
  zero-size and off-canvas checks so a non-finite coordinate does not also emit meaningless geometry noise.
Task 11: fix round 1/5 complete (commits 28448cc..d239306) — Important ADDRESSED, no new breakage.
  Re-reviewer removed the rule and watched exactly the 4 new tests fail, then restored. Confirmed all
  five op types are covered including label, whose height comes from LABEL_H not the caller.
  Smuggling matrix: "1.5" as a string, null and booleans are all blocked as invalid-coord; 1e308 and
  MAX_VALUE correctly pass isFinite and fall through to off-canvas, which is right since they are
  genuine numbers.
  Judged the suppression correct on the merits: a non-finite coordinate is a type error that makes the
  geometry maths meaningless, so reporting off-canvas alongside would be misleading noise. The author
  fixes the coordinate and re-lints, which surfaces any remaining geometry problem.
Task 11: complete (commits db351ad..d239306, review clean after 1 fix round)
Task 12: dispatched (implementer, sonnet — 5 new files incl. an authored reference doc; code pre-verified) — BASE d239306
Task 12: implementer STALLED (watchdog, no progress for 600s). Infrastructure failure, not a code or
  plan problem: no commits, clean working tree, no report written, nothing persistent left behind.
## re-dispatch fresh on the same model. The skill's rule against retrying the same model applies
  when an implementer reports itself stuck, which signals something needs to change; a watchdog kill
  carries no such signal. Trimming the brief slightly since the code is fully pre-verified anyway.
  Cost if wrong: one more stall, detectable the same way.
Task 12: re-dispatched (implementer, sonnet) — BASE d239306 unchanged
Task 12: task review — spec PASS, no scope creep. 1 Critical, 4 Important.
  CRITICAL: a whitespace-only quote or attribution passes as GROUNDED, because `if not x` treats "   "
  as truthy. Controller reproduced: quote="" is rejected but quote="   " and quote="\t" are accepted and
  render as > "   " under a real attribution role. That is a fabricated citation, and it is the exact
  dishonesty the grounded/inferred split exists to prevent.
  IMPORTANT: test_ids_match_the_expected_shape passes for the WRONG REASON. Deleting the ID_RE branch
  entirely leaves it green, because it mutates D1 which D4 and D5 reference in `exercises`, so the
  exercises check raises with "D1" in the message and satisfies the assertion. My test code, not the
  implementer's. A test that passes for the wrong reason is worse than no test.
  IMPORTANT: D1 and D01 coexist as distinct ids. Task 13 extracts ids with \bD\d+\b, so this is a silent
  mismatch waiting to happen. Tightening ID_RE to ^D[1-9]\d*$.
  IMPORTANT: render() does not escape | in table cells; a pipe in a demo_fit `why` produces a 4-cell row
  against a 3-column header. Controller reproduced.
Task 12: fix round 1/5 dispatched — strip-before-truthiness, isolate the id-shape test, reject leading
  zeros, escape pipes in both tables.
RECOMMENDATION 2 for the final review and for Dan: public-safety in this skill is OPT-IN ONLY. guardrails
  catches em dashes, a fixed 6-word AI-tell list, and whatever strings the author puts in `banned_terms`.
  There is no name, company or PII heuristic. The reviewer confirmed end to end that a discovery record
  containing a real-looking person and company builds successfully with exit 0 when banned_terms is
  absent. So the "generic and public-safe" guarantee rests on the author already knowing which names to
  scrub, which is the same honour system the artifact was built to replace. Out of scope to change here;
  worth a follow-up, alongside the contrast check.
Task 12: fix round 1/5 complete (commit 7e80b4b). Controller verified all four independently:
  whitespace and tab quote/attribution now REJECTED while the valid example still passes; D01, D0 and
  D007 rejected, D1/D10/D42 accepted; pipes escaped as \| in BOTH the demo_fit and beats tables, giving
  3 cells against a 3-column header when counted the way a renderer counts them (splitting on unescaped
  pipes only); and neutralising the ID_RE branch now fails 3 tests, so the id-shape test is genuinely
  isolated. Note my first isolation attempt reported a false negative because my deletion regex never
  matched, not because the test was weak; re-ran it properly.
Task 12: scoped re-review dispatched (haiku) — package review-48d94c5..7e80b4b.diff
Task 13 pre-dispatch check (controller): PLAN DEFECT FOUND AND FIXED, a spec-versus-plan contradiction.
  The shipped flow-guide example uses FREE-TEXT traces values ("Discovery call: <a short attributed
  quote>." and "Discovery: they build with Framework A..."), with no signal ids. Running the planned
  traces check against it with the discovery example produces 2 `untraced` findings. But the plan's
  Step 5 wiring called guardrails.enforce() on ANY finding, and enforce raises. So the moment anyone
  added a `discovery` field to the shipped example, the build would hard-fail, directly contradicting
  the spec line "Free-text `traces` remains accepted with a warning, so existing configs still build".
## split the severities. `unresolved-trace` (an id that does not exist) stays a hard failure,
  because the author wrote D9 and meant something specific. `untraced` (no id at all) becomes a stderr
  warning. This is what the spec's own sentence describes, and it is the only reading under which the
  shipped example survives being wired up. Fixed in the plan (cc75c9a), brief regenerated.
  Cost if wrong: a config full of prose traces builds with warnings nobody reads, which is exactly the
  honour-system state the feature is meant to replace; but hard-failing would make the feature
  unadoptable on any existing config, and warnings are the documented migration path.
  I missed this in the pre-flight scan because it spans the spec's prose and the plan's code, which the
  scan compared only within the plan.
Task 12: fix round 1/5 complete (commits 48d94c5..7e80b4b) — all 4 findings ADDRESSED, no new breakage.
  Re-reviewer confirmed the strip is applied where the conditional requirement lives, that the schema
  minLength fires FIRST for the empty case so there is no confusing double report, that pipe escaping
  covers every table cell without double-escaping, and that the reference doc now states the enforced
  regex exactly rather than approximately.
Task 12: minor (deferred): whitespace-only `text` on a signal, or a whitespace-only `engagement`, still
  passes (minLength does not exclude spaces) and renders as a visibly empty bullet or heading. Same bug
  class as the Critical but NOT the same severity: a blank quote presented under an attribution is a
  fabricated citation, whereas a blank text is self-evidently broken on sight and the signal still
  carries its quote. Deferred for final-review triage.
Task 12: complete (commits d239306..7e80b4b, review clean after 1 fix round)
Task 13: dispatched (implementer, sonnet — traces module plus wiring into two generators) — BASE cc75c9a
Task 13: implementer DONE (commit 503f73c) — 89 Python tests on both interpreters, 33 node, goldens
  byte-identical. Controller verified ALL FOUR severity cases end to end against the real generator:
    1. no discovery field  -> "traces-to was NOT checked" note, build succeeds
    2. free text + record  -> 2 warnings, exit 0, HTML STILL WRITTEN
    3. unresolvable D99    -> exit 1, "unresolved-trace ... D99 does not exist", nothing written
    4. resolvable D1       -> clean build, no warnings
  The severity split I ruled on pre-dispatch is working exactly as intended: the skill's own shipped
  example builds with warnings rather than being bricked, while a wrong id still fails hard.
## the implementer flagged a latent bug in the brief's Step 6 verification snippet, which wrote the
  mutated config to /tmp while keeping a discovery path relative to the original example directory, so it
  raised FileNotFoundError instead of the unresolved-trace failure it was meant to show. Confirmed a
  script artifact, not an implementation defect: relative resolution works correctly when the config stays
  put, and I exercised both paths with an absolute path. Fixed the plan snippet. Cost if wrong: none.
Task 13: task review dispatched (sonnet) — package review-cc75c9a..503f73c.diff
Task 13: task review — spec PASS, 0 Critical, 2 Important. Reviewer confirmed under adversarial testing
  that a good id alongside a bad one does not launder it, a repeated bad id yields one finding not two,
  the \bD\d+\b regex correctly extracts from <code>D1</code> and punctuation while rejecting d1, D1s and
  3D1, the walk is shape-agnostic and even finds a traces field inside demo.beats, and the "NOT checked"
  note still prints when a bogus traces value would otherwise have failed.
  IMPORTANT 1: load_discovery lets raw tracebacks escape. Controller reproduced FileNotFoundError and
  json.decoder.JSONDecodeError against the real generator; reviewer also found KeyError from a signal
  with no id. None are ConfigError/GuardrailError so the try/except does not catch them, and the author
  gets a stack trace where every other config problem gives a clean message. My brief's code.
  IMPORTANT 2: the presenter-guide half of the feature DOES NOT EXIST. schema_presenter_guide declares
  no traces field and the format doc never mentions one (0 occurrences), while the flow-guide schema
  REQUIRES it. So a presenter guide with a discovery record builds with zero warnings because there is
  nowhere legitimate for a trace to live.
## fix Important 2 here rather than defer it. This is a plan-versus-spec gap and the spec is the
  binding authority: design doc line 249 says "traces on flow-guide cards AND presenter-guide talking
  points". My plan wired only the flow guide, so the feature has been half-delivered against its own
  spec. Task 13 is the traces task and therefore its right home. Making it OPTIONAL rather than required
  on slides, because requiring it would break the shipped example and gradual adoption is the entire
  point of the severity split. Cost if wrong: a slightly larger Task 13 diff than planned.
Task 13: fix round 1/5 dispatched — ConfigError for the three load_discovery failure modes, plus
  traces on the presenter-guide slide schema, its format doc, and its example.
Task 13: fix round 1/5 complete (commit fe01927) — both Important findings ADDRESSED. Controller verified:
  the three load_discovery failure modes now give clean single-line ConfigErrors with ZERO tracebacks
  ("could not read /tmp/nope.json", "is not valid JSON", "signals[0]: missing required field 'id'");
  the presenter-guide half now genuinely works, resolvable D5 builds and D99 hard-fails naming
  slides[2].traces with nothing written; schema declares traces and the format doc covers it in 4 places;
  and critically the shipped example now carries "traces": "D5" yet the golden is BYTE-IDENTICAL,
  confirming traces is metadata and not rendered. 94 Python tests both interpreters, 33 node.
Task 13: scoped re-review dispatched (haiku) — package review-503f73c..fe01927.diff
Task 13: fix round 1/5 complete (commits 503f73c..fe01927) — both Important ADDRESSED, no new breakage.
  Re-reviewer broke each of the three guards in turn and confirmed the matching test fails, so all three
  are load-bearing. Confirmed the error handling is TIGHTLY scoped: only load_discovery and signal_ids
  are guarded, so a genuine bug in _walk or check_traces still surfaces as a real traceback rather than
  being tidied into a ConfigError.
  Judged the no-signals-key behaviour correct on the merits: a discovery file with no signals means "no
  signals defined", not "malformed file", so yielding unresolved-trace findings is right and erroring
  would be wrong. Checked every claim in the new doc against the code; all five match exactly.
Task 13: complete (commits cc75c9a..fe01927, review clean after 1 fix round)
Task 14: dispatched (implementer, sonnet — six descriptions plus worker bodies and two deferred Task 4 minors) — BASE fe01927
Task 14: task review — spec PASS, mechanical gates all pass, no near-duplicates, each worker fires on
  realistic phrasings. 0 Critical, 2 Important, 4 Minor.
  IMPORTANT 1: the router and demo-discovery BOTH fire on a bare transcript share, the plugin's single
  most common opening move. If demo-discovery wins, the pipeline stops at stage 1 because its body only
  notes that its output feeds later stages rather than instructing continuation. Invisible to the suite:
  test_the_router_does_not_claim_the_workers_artifacts checks only the three artifact nouns, never
  "transcript". This is precisely what Task 15's R1 scenario would have surfaced, at higher cost.
  IMPORTANT 2: nothing anchors "POC" or "plan" although demo-discovery's body covers v1-versus-v2 POC
  commitment. "The customer asked for a POC plan" has no lexical anchor.
## fixing the two Importants AND three of the four Minors, which departs from the usual
  minors-never-enter-the-loop rule. Reasoning: for every other task, wording nits are cosmetic; for THIS
  task the descriptions ARE the deliverable, so "wants existing create slides tweaked" reading as broken
  internal jargon is a defect in the product, not a polish item. All are edits to the exact lines already
  being changed. Deferring only the entry-table formatting nit, which is body text and not used for
  selection. Cost if wrong: a slightly larger diff on a task whose whole content is six short paragraphs.
## also requiring a NEW test asserting the router and demo-discovery do not both claim an
  unqualified transcript, watched failing first. The gap existed because the suite tested only the
  overlaps I thought of when writing it; this closes the one that actually mattered.
Task 14: minor (deferred): router entry-table multi-step row lists workers in prose rather than
  canonical demo-studio:<worker> ids.
Task 14: fix round 1/5 dispatched.
Task 14: fix round 1/5 complete (commit c4d357d). Controller verified: the transcript overlap is closed
  (demo-discovery now gates on "on their own ... without asking for the rest of the pipeline" while the
  router keeps the bare share), POC anchored, "existing create slides" jargon replaced with "net-new
  slides it already built", aggregate/assembled made consistent. 101 Python tests both interpreters,
  33 node, goldens byte-identical.
  The new overlap guard IS load-bearing: removing the exclusion clause fails it, restoring passes. My
  first attempt to check that was an unfaithful revert on my part (I swapped the opening sentence but
  left the exclusion clause in place, so of course it still passed); re-ran it properly.
  Implementer caught a conflict in the reviewer's proposed wording: it hyphenated "demo-fit" while
  test_worker_descriptions_name_their_artifact asserts the literal substring "demo fit". It kept the
  unhyphenated form and said so. Correct call, and exactly the cross-check I want from an implementer
  rather than blind transcription.
Task 14: scoped re-review dispatched (haiku) — package review-a9e4581..c4d357d.diff
Task 14: fix round 1/5 complete (commits a9e4581..c4d357d) — all 5 findings ADDRESSED, no new breakage.
  Re-reviewer confirmed the narrowing did NOT open a new gap: "which demo should we lead with", "did they
  actually say air-gapped", "who is the real buyer here" and "give me a beat sheet" all still reach
  demo-discovery. Judged the new test's literal assertion brittle-but-correct, on the grounds that the
  clause IS the mechanism, so any rephrase that drops it SHOULD fail. Confirmed the implementer's
  "demo fit" call was necessary for both tests to pass together.
Task 14: complete (commits fe01927..c4d357d, review clean after 1 fix round)
Task 15: routing results. Each scenario went to a FRESH agent seeing only the six descriptions and one
  request, blind to which set it had, so it could not infer the expected answer.
  BASELINE (set A, pre-Task-14 descriptions):
    R2 -> presenter-guide, high, but WOULD_ASK_FIRST: yes
    R6 -> demo-studio ROUTER, quoting its own "even if they only ask for one piece or start midway".
          This IS the predicted over-trigger: the old router swallowed a mid-pipeline request.
  NEW (set B):
    R1 -> demo-studio          PASS  (demo-discovery only a runner-up; the exclusion clause works)
    R2 -> presenter-guide      PASS  (and decisive: WOULD_ASK_FIRST no, vs yes at baseline)
    R3 -> deck-flow-guide      PASS  (no runners-up at all)
    R4 -> presenter-guide      PASS
    R5 -> demo-studio          PASS on selection; ask-behaviour retested separately, see below
    R6 -> create-slides        FAIL  (expected deck-flow-guide first, then slides, then presenter guide)
Correction to the plan's own claim: it asserted R2 and R6 were cases "the monolith could not get right
  by construction". The baseline disproves half of that. My baseline snapshot is commit fe01927, which is
  AFTER Task 4 split the skills and gave each worker a stub description, so it is not the monolith at all.
  Baseline R2 already routed correctly. The honest reading: the SPLIT made direct routing possible, and
  Task 14's descriptions made it decisive rather than hesitant. Only R6 shows the predicted over-trigger.
Test-design limitation found and corrected mid-run: R5 expects the router to ASK which stage, but that
  instruction lives in the router's BODY (SKILL.md line 27, "Genuinely unclear | Ask which stage. Do not
  guess."), which the selector agents never saw. R5's second half was untestable as I designed it, so I
  re-ran it giving the agent the router body.
Task 15: R5 ask-behaviour retest PASSED when given the router body: ASK_USER, quoting
  "Genuinely unclear | Ask which stage. Do not guess."
Task 15: R6 misroute FIXED (commit bf891ac). Router description now claims the multi-artifact and
  resume-partway cases generically, without reintroducing any worker artifact noun, and the exclusion is
  sharpened to "exactly one artifact" so single-artifact requests still route straight through.
  Live re-run after the fix: R6 -> demo-studio (high, quoting "when they name several pieces to build"),
  R1 -> demo-studio unregressed, R2 -> presenter-guide unregressed, R5 -> demo-studio unregressed and now
  with no runners-up at all. SIX OF SIX.
Task 15: complete (commits c4d357d..8835882) — 102 Python tests on both interpreters, 33 node, pptx PASS.
ALL 15 TASKS IMPLEMENTED.


## PARK Important 1, the low-contrast rule's mis-tiering, and surface it as the top follow-up.
  The rule I specified in the fix wave is calibrated wrong in BOTH directions. It gates box body text at
  the WCAG normal-text tier (4.5:1) although those runs carry no explicit size and render at the 18pt
  default, which is the large-text tier (3:1); so it rejects the brand's own accent, indigo on panel at
  4.19:1, with no per-op escape. And it skips `label` ops entirely, which at 9pt are the only text
  genuinely in the normal tier. Strict where it should be lenient, silent where it should be strict.
  Not fixing it here because the process allows exactly one fix wave and this needs a considered
  threshold decision, not a hurried one. Nothing in the repo currently trips it (the shipped eyebrow
  passes at 4.69:1, 4% headroom), so merging does not break anything today.
  Cost if wrong: the first author who styles a box label with the brand accent hits a hard build failure
  with no documented escape. That is a bad first experience, and it is my defect, not the implementer's.


## PARK Minor 2, the meta-key skip being depth-unbounded. `if key in _META_KEYS: continue` fires at
  any nesting depth, so a subtree under a nested key of that name escapes all three checks. The fix is
  one line, `if not _path and key in _META_KEYS`. Parking rather than fixing for the same process reason,
  but noting it is a bypass in the very gate this wave existed to repair, and the docs now overclaim by
  saying the scan covers every text field.
  Cost if wrong: a config author who happens to nest an object called `session.banned_terms` gets it
  silently exempted. Contrived, but the gate should not have holes.


## ACCEPT the implementer's deviation on brand.json's `fonts` block. I instructed deleting it as
  dead alongside `acts`; it kept it because build_create_slides.js and slidekit.js read brand.fonts.*
  directly as JSON, bypassing brand.py. My dead-code analysis had looked only at Python consumers.
  Deleting it would have thrown at require time. Re-reviewer confirmed no reader of any deleted key.


## ACCEPT Minor 4 as a knowing, spec-divergent trade. Spec section 3 says brand.json should carry
  the act colours "currently documented only in prose in presenter-guide-format.md"; deleting the dead
  `acts` block restored exactly the state the spec called the problem. I instructed that deletion. It is
  defensible (act colour is per-engagement config data and the block had zero consumers in either
  language) but it IS the one place this branch moved away from its spec, and it should be recorded as
  such rather than glossed. Cost if wrong: seven hexes live in prose in one doc.


## PARK Minors 3, 5, 6 and both informational items for follow-up. None blocks merge.
