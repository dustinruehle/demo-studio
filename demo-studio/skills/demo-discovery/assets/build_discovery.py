#!/usr/bin/env python3
# demo-studio/skills/demo-discovery/assets/build_discovery.py
"""Render discovery.json to a readable Markdown record.

The JSON is the durable artifact that later stages reference by signal id; this
Markdown is the version a human reads. Stdlib only, Python 3.9 compatible.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "shared"))
import guardrails       # noqa: E402
import validate_config  # noqa: E402

import schema_discovery  # noqa: E402

ID_RE = re.compile(r"^D[1-9]\d*$")


class DiscoveryError(Exception):
    """Raised when the signal set is internally inconsistent."""


def check_signals(cfg):
    """Rules the schema dialect cannot express."""
    seen = set()
    problems = []
    for i, signal in enumerate(cfg["signals"]):
        sid = signal["id"]
        if not ID_RE.match(sid):
            problems.append("signals[%d].id: %r must look like D1, D2, D3" % (i, sid))
        if sid in seen:
            problems.append("signals[%d].id: duplicate id %r" % (i, sid))
        seen.add(sid)
        if signal["kind"] == "grounded":
            for field in ("quote", "attribution"):
                value = signal.get(field)
                if not isinstance(value, str) or not value.strip():
                    problems.append(
                        "signals[%d] (%s): a grounded signal needs %s, "
                        "otherwise it is inferred" % (i, sid, field))
    for i, signal in enumerate(cfg["signals"]):
        for ref in signal.get("exercises", ()):
            if ref not in seen:
                problems.append(
                    "signals[%d].exercises: %s does not exist" % (i, ref))
    if problems:
        raise DiscoveryError("%d problem(s):\n  %s" % (len(problems), "\n  ".join(problems)))


def _cell(value):
    """Escape a value for placement inside a Markdown table cell.

    A literal pipe would otherwise be read as a column boundary and silently
    misalign the row.
    """
    return str(value).replace("|", "\\|")


def render(cfg):
    """Markdown, grounded signals first so provenance reads at a glance."""
    out = ["# Discovery record: %s" % cfg["engagement"], ""]

    for kind, heading in (("grounded", "Grounded (they said it)"),
                          ("inferred", "Inferred (we designed it)")):
        rows = [s for s in cfg["signals"] if s["kind"] == kind]
        if not rows:
            continue
        out += ["## %s" % heading, ""]
        for s in rows:
            out.append("**%s** %s" % (s["id"], s["text"]))
            if s.get("quote"):
                out.append('> "%s"' % s["quote"])
                out.append("> %s" % s.get("attribution", "unattributed"))
            if s.get("exercises"):
                out.append("Exercises: %s" % ", ".join(s["exercises"]))
            out.append("")

    if cfg.get("demo_fit"):
        out += ["## Demo fit", "", "| Demo | Why | Verdict |", "|---|---|---|"]
        for row in cfg["demo_fit"]:
            out.append("| %s | %s | %s |" % (
                _cell(row["demo"]), _cell(row["why"]), _cell(row["verdict"])))
        out.append("")

    session = cfg.get("session") or {}
    if session.get("beats"):
        out += ["## Session design", "",
                "Pitch: %s. Deployment: %s." % (
                    "yes" if session.get("pitch") else "no",
                    session.get("deployment", "unstated")),
                "", "| Start | Beat | Minutes |", "|---|---|---|"]
        for start, name, mins in session["beats"]:
            out.append("| %s | %s | %s |" % (_cell(start), _cell(name), _cell(mins)))
        out.append("")

    fork = cfg.get("fork") or {}
    if fork:
        out += ["## v1 or v2", "",
                "Choice: **%s**. %s" % (fork.get("choice", "unstated"),
                                        fork.get("why", "")), ""]
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: build_discovery.py CONFIG.json [OUT.md]\n")
        sys.exit(1)
    cfg_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "discovery.md"
    with open(cfg_path) as f:
        cfg = json.load(f)
    validate_config.enforce(cfg, schema_discovery.SCHEMA,
                            name=os.path.basename(cfg_path))
    check_signals(cfg)
    guardrails.enforce(guardrails.check_tree(
        cfg, allowlist=cfg.get("allow_words", ()), banned=cfg.get("banned_terms", ())))
    text = render(cfg)
    with open(out_path, "w") as f:
        f.write(text)
    print("wrote %s with %d signal(s)" % (out_path, len(cfg["signals"])))


if __name__ == "__main__":
    try:
        main()
    except (validate_config.ConfigError, guardrails.GuardrailError, DiscoveryError) as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)
