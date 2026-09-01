---
name: build-spec
description: >-
  Use when the user asks to spec a customer demo, write a build spec, or produce
  something a coding agent can execute end to end to build a demo.
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

Apply the disciplines in `../../shared/grounding.md`.
