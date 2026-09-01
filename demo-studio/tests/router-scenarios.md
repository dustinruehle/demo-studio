# Router behaviour scenarios

Each scenario is dispatched to a fresh subagent that sees only the six skill
descriptions and one user request, and is asked which skill it would select.
The agent is not told which description set it has, so it cannot infer the
expected answer from context.

| # | Prompt | Expected |
|---|---|---|
| R1 | "Here's the transcript from our call with the platform team." plus a transcript | router `demo-studio`, offering the full pipeline |
| R2 | "Make me a presenter guide for this deck." | `presenter-guide` directly, no discovery stage forced |
| R3 | "Reorder this deck for a security team audience." | `deck-flow-guide` |
| R4 | "Add the demo walkthrough to the guide." | `presenter-guide`, demo block only |
| R5 | "Help me with a customer demo." | router `demo-studio`, and it ASKS which stage rather than guessing |
| R6 | "I know the demo already, build the deck and the guides." | `deck-flow-guide` first, then create-slides and presenter-guide; discovery and build-spec skipped |

R2 and R6 are the ones the pre-restructure monolith could not get right by
construction: with one description covering all five jobs, there was nothing for
a direct single-artifact request to match against.

## Results, 2026-09-01

Method: each scenario went to a fresh agent that saw only the six descriptions
and one user request, blind to which description set it held. R5's second half
needed a separate run, because "ask which stage" lives in the router's body and
a selector working from descriptions alone can never exhibit it.

### Baseline, descriptions as of commit fe01927

| # | Selected | Note |
|---|---|---|
| R2 | `presenter-guide` | already correct, but hedged: WOULD_ASK_FIRST yes |
| R6 | `demo-studio` | over-triggered, quoting "even if they only ask for one piece or start midway" |

A correction to this plan's own claim. It asserted R2 and R6 were both cases the
monolith "could not get right by construction". That is only half true. This
baseline is taken after Task 4 had already split the skills and given each worker
a stub description, so it is not the monolith. R2 already routed correctly there.
The split is what made direct routing possible; the descriptions made it decisive.

### First run, descriptions as of commit c4d357d

| # | Selected | Verdict |
|---|---|---|
| R1 | `demo-studio` | pass, `demo-discovery` only a runner-up |
| R2 | `presenter-guide` | pass, and decisive where the baseline hedged |
| R3 | `deck-flow-guide` | pass, no runners-up at all |
| R4 | `presenter-guide` | pass |
| R5 | `demo-studio` | pass on selection; asks correctly when given the body |
| R6 | `create-slides` | FAIL, expected the router to sequence three artifacts |

R6 diagnosis: the router's entry table already handled this exact case, but its
description did not claim it, and selection never reaches a body it did not
select. Narrowing the router in the previous round fixed direct single-artifact
requests and opened this gap.

### After the fix, commit bf891ac

| # | Selected | Verdict |
|---|---|---|
| R1 | `demo-studio` | pass, unregressed |
| R2 | `presenter-guide` | pass, unregressed |
| R5 | `demo-studio` | pass, unregressed, and now with no runners-up |
| R6 | `demo-studio` | pass, quoting "when they name several pieces to build" |

Six of six. The router now claims the multi-artifact and resume-partway cases
generically, without naming any worker artifact, so the single-artifact
exclusion still holds.
