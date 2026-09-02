"""Schema for a presenter-guide config. See references/presenter-guide-format.md."""

_STRINGS = {"type": "array", "items": {"type": "string"}}

_SLIDE = {
    "type": "object",
    "required": ["num", "act", "short", "title"],
    "properties": {
        "num": {"type": ["number", "string"]},
        "act": {"type": "string", "minLength": 1},
        "short": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "onscreen": {"type": "string"},
        "points": _STRINGS,
        "say": _STRINGS,
        "ask": _STRINGS,
        "traces": {"type": "string"},
    },
}

_BEAT = {
    "type": "object",
    "required": ["id", "title", "rows"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "badge": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "tag": {"type": "string"},
        "accent": {"type": "string", "enum": ["indigo", "coral", "green", "amber"]},
        "term": {"type": "string"},
        "rows": {"type": "array"},
        "note": {"type": "string"},
        "nav": {"type": "string"},
    },
}

_DEMO = {
    "type": "object",
    "properties": {
        "nav_divider": {"type": "string"},
        "banner": {"type": "object"},
        "talk_track": {"type": "string"},
        "lanes": {"type": "array"},
        "termmap": {"type": "array"},
        "smoke": {"type": "string"},
        "beats": {"type": "array", "items": _BEAT},
        "scenarios": {"type": "array"},
        "switches": {"type": "array"},
        "switch_note": {"type": "string"},
        "troubleshooting": {"type": "array"},
    },
}

SCHEMA = {
    "type": "object",
    "required": ["tab_title", "title", "acts", "slides"],
    "properties": {
        "tab_title": {"type": "string", "minLength": 1},
        "nav_title": {"type": "string"},
        "nav_sub": {"type": "string"},
        "eyebrow": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "subtitle": {"type": "string"},
        "chips": {"type": "array"},
        "legend": {"type": "array"},
        "acts": {"type": "object"},
        "slides": {"type": "array", "items": _SLIDE},
        "demo": _DEMO,
        "discovery": {"type": "string"},
        "allow_words": _STRINGS,
        "banned_terms": _STRINGS,
    },
}
