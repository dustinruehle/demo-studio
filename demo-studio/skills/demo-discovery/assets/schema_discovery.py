# demo-studio/skills/demo-discovery/assets/schema_discovery.py
"""Schema for discovery.json. See references/discovery-format.md."""

_SIGNAL = {
    "type": "object",
    "required": ["id", "kind", "text"],
    "properties": {
        "id": {"type": "string", "minLength": 2},
        "kind": {"type": "string", "enum": ["grounded", "inferred"]},
        "text": {"type": "string", "minLength": 1},
        "quote": {"type": "string"},
        "attribution": {"type": "string"},
        "exercises": {"type": "array", "items": {"type": "string"}},
    },
}

SCHEMA = {
    "type": "object",
    "required": ["engagement", "signals"],
    "properties": {
        "engagement": {"type": "string", "minLength": 1},
        "signals": {"type": "array", "items": _SIGNAL},
        "demo_fit": {"type": "array", "items": {
            "type": "object",
            "required": ["demo", "why", "verdict"],
            "properties": {
                "demo": {"type": "string"},
                "why": {"type": "string"},
                "verdict": {"type": "string", "enum": ["lead", "second", "skip"]},
            },
        }},
        "session": {"type": "object"},
        "fork": {"type": "object"},
    },
}
