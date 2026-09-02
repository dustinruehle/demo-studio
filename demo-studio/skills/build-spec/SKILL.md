---
name: build-spec
description: >-
  Use when someone wants a build spec, wants a customer demo specified so a
  coding agent can build it end to end, or asks what to hand an engineer to make
  the demo real.
---

# Build Spec

Read `references/build-spec.md`, then fill `assets/build_spec_template.md`.
Non-negotiables: name the skills/refs to read with "reference wins", a preflight
that installs prereqs, a definition-of-done gate whose tests loop until green,
mock-by-default, generic/public-safe, pinned pre-release versions.

## Quickstart (hand to a coding agent)

```bash
cp assets/build_spec_template.md BUILD_SPEC.md
# fill it in (see references/build-spec.md)
```

Apply the disciplines in `shared/grounding.md`.
