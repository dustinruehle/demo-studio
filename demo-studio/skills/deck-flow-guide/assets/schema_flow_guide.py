"""Schema for a flow-guide config. See references/flow-guide-format.md."""

_PAIR = {"type": "array", "items": {"type": "string"}}

_PREVIEW = {
    "type": "object",
    "required": ["eyebrow", "title", "body"],
    "properties": {
        "eyebrow": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "sub": {"type": "string"},
        "body": {"type": "string", "minLength": 1},
    },
}

_CARD = {
    "type": "object",
    "required": ["type", "seq", "title", "why", "traces"],
    "properties": {
        "type": {"type": "string", "enum": ["deck", "create"]},
        # seq and act.no are STRINGS in the shipped example ("01", "02"), not numbers.
        # Accept both so the example validates and a numeric config still works.
        "seq": {"type": ["number", "string"]},
        "title": {"type": "string", "minLength": 1},
        "why": {"type": "string", "minLength": 1},
        "traces": {"type": "string"},
        "src_label": {"type": "string"},
        "deckid_label": {"type": "string"},
        "deckid_quote": {"type": "string"},
        "deckid_pg": {"type": "string"},
        "preview": _PREVIEW,
    },
}

_ACT = {
    "type": "object",
    "required": ["no", "title", "cards"],
    "properties": {
        "no": {"type": ["number", "string"]},
        "title": {"type": "string", "minLength": 1},
        "purpose": {"type": "string"},
        "time": {"type": "string"},
        "cards": {"type": "array", "items": _CARD},
    },
}

SCHEMA = {
    "type": "object",
    "required": ["tab_title", "title", "acts"],
    "properties": {
        "tab_title": {"type": "string", "minLength": 1},
        "eyebrow": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "subtitle": {"type": "string"},
        "chips": {"type": "array", "items": _PAIR},
        "legend": {"type": "object"},
        "acts": {"type": "array", "items": _ACT},
        "footer": {"type": "object"},
        "discovery": {"type": "string"},
        "allow_words": {"type": "array", "items": {"type": "string"}},
        "banned_terms": {"type": "array", "items": {"type": "string"}},
    },
}
