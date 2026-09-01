"""Resolve traces-to references against the discovery record.

Every flow-guide card and presenter-guide slide claims to trace back to a
discovery signal. Free text made that unverifiable. Signal ids make it a
resolvable reference, so a card that traces to nothing is a build finding.
"""
import json
import re

import validate_config
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
    """Every signal id in a discovery record. Missing 'signals' is a legitimate
    empty record (yields an empty set); a signal present but missing 'id' is a
    malformed discovery file and raises, naming the offending entry."""
    out = set()
    for i, signal in enumerate((discovery or {}).get("signals", ())):
        if "id" not in signal:
            raise validate_config.ConfigError(
                "discovery: signals[%d]: missing required field 'id'" % i)
        out.add(signal["id"])
    return out


def load_discovery(path):
    """Load a discovery JSON file. Bad path or bad JSON becomes a ConfigError
    naming the path, the same clean-message contract every other config problem
    in this tool honours, rather than a raw traceback."""
    try:
        with open(path) as f:
            text = f.read()
    except OSError as err:
        raise validate_config.ConfigError(
            "discovery: could not read %s (%s)" % (path, err.strerror or err))
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise validate_config.ConfigError(
            "discovery: %s is not valid JSON (%s)" % (path, err))


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
