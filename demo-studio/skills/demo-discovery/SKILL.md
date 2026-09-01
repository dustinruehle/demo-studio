---
name: demo-discovery
description: >-
  Use when someone wants a transcript's demo signals pulled out on their own,
  which demo to lead with or skip, who is really in the room, the stated stack
  or constraints, a demo fit analysis, a session beat sheet, a grounded versus
  inferred record of what was said, or wants to scope a single-demo v1 versus
  a fused POC-commitment v2, without asking for the rest of the pipeline.
---

# Demo Discovery

Read the discovery/call transcript(s) and turn it into a demo direction: who is
really in the room, what to build, and how the session should be shaped. This is
the first stage of the pipeline; its output feeds `demo-studio:build-spec` and
`demo-studio:deck-flow-guide`.

## 1. Discovery read

Read the call transcript(s). Identify the real technical buyer versus low-fit
contacts. Pull: their stack/frameworks, stated pains (quote them), constraints
(security, regulated, air-gapped), deployment reality (cloud vs self-host), who
will be in the room, and any productization thesis. Separate what was *said*
from what you *infer*.

## 2. Demo-fit analysis

Map candidate out-of-the-box demos to the stated needs, with a one-line "why"
each, and say which to lead with and which to skip. Name the audience's
familiarity so you can right-size depth (skip a product pitch if they already
know it).

## 3. Session design

Decide pitch-or-no-pitch, cloud-primary vs local, and draft a time-boxed beat
sheet (for example 60 min) before touching architecture. Pick the demo domain
from THEIR heavy verticals, not a default.

## 4. v1 vs v2 fork (for multi-demo stories)

v1 = one narrative/domain with the OOTB demos themed and sequenced (cheap,
robust, independent failure surfaces). v2 = one fused build (higher fidelity,
higher risk; only with a POC/commitment). Default to v1 for a first session.

Apply the disciplines in `../../shared/grounding.md`.
