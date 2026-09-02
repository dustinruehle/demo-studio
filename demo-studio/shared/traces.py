"""Resolve traces-to references against the discovery record.

Every flow-guide card and presenter-guide slide claims to trace back to a
discovery signal. Free text made that unverifiable. Signal ids make it a
resolvable reference, so a card that traces to nothing is a build finding.
"""
import json
import os
import re
import sys

import validate_config
from guardrails import Violation, enforce

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
    """Return violations for traces fields. No discovery record means no check.

    The short-circuit is `discovery is None`, not falsiness: a discovery.json
    that parses to `{}` was still LOADED (the config named a real, readable
    file), so it should walk and report every unresolved traces value, the
    same as any other discovery record with no matching signals. `not
    discovery` would treat that {} the same as "no discovery field at all"
    and silently skip the check the author asked for.
    """
    if discovery is None:
        return []
    out = []
    _walk(config, signal_ids(discovery), "", out)
    return out


def resolve_and_report(cfg, cfg_path, stream=None):
    """Load the optional discovery record a config points at, check every
    `traces` value against it, warn or hard-fail, and report. Shared by both
    guide generators so the severity split (an unresolved id hard-fails, free
    text only warns) and the "not checked" note live in exactly one place;
    F10's discovery-record-parses-to-{} fix then also lives in one place.

    Raises GuardrailError, the same exception every other guardrail in this
    skill raises, so a single except clause in the caller covers this too.
    """
    if stream is None:
        stream = sys.stderr
    discovery = None
    if cfg.get("discovery"):
        discovery_path = cfg["discovery"]
        if not os.path.isabs(discovery_path):
            discovery_path = os.path.join(os.path.dirname(cfg_path), discovery_path)
        discovery = load_discovery(discovery_path)
    found = check_traces(cfg, discovery)
    # Two severities, deliberately. An id that does not resolve is an error: the
    # author wrote D9 and meant something. A traces value with no id at all is a
    # warning: the spec says free-text traces stays accepted so existing configs
    # still build. Hard-failing both would break the shipped example, which uses
    # prose traces, the moment anyone wires a discovery record in.
    hard = [v for v in found if v.check == "unresolved-trace"]
    soft = [v for v in found if v.check == "untraced"]
    for v in soft:
        stream.write("warning: %s: %s\n" % (v.field, v.detail))
    if discovery is None:
        stream.write(
            "note: no 'discovery' field in the config, so traces-to was NOT checked\n")
    if hard:
        enforce(hard)
