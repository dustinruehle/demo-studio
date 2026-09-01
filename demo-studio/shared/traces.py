"""Resolve traces-to references against the discovery record.

Every flow-guide card and presenter-guide slide claims to trace back to a
discovery signal. Free text made that unverifiable. Signal ids make it a
resolvable reference, so a card that traces to nothing is a build finding.
"""
import json
import re

from guardrails import Violation

REF_RE = re.compile(r"\bD\d+\b")


def refs(text):
    """Signal ids in a string, in order, deduplicated."""
    if not isinstance(text, str):
        return []
    out = []
    for match in REF_RE.findall(text):
        if match not in out:
            out.append(match)
    return out


def signal_ids(discovery):
    return {s["id"] for s in (discovery or {}).get("signals", ())}


def load_discovery(path):
    with open(path) as f:
        return json.load(f)


def _walk(obj, known, path, out):
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = key if not path else "%s.%s" % (path, key)
            if key == "traces" and isinstance(value, str):
                found = refs(value)
                if not found:
                    out.append(Violation(
                        "untraced", child,
                        "no signal id, every card should trace to a D-number"))
                for ref in found:
                    if ref not in known:
                        out.append(Violation(
                            "unresolved-trace", child, "%s does not exist" % ref))
            else:
                _walk(value, known, child, out)
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            _walk(value, known, "%s[%d]" % (path, i), out)


def check_traces(config, discovery):
    """Return violations for traces fields. No discovery record means no check."""
    if not discovery:
        return []
    out = []
    _walk(config, signal_ids(discovery), "", out)
    return out
