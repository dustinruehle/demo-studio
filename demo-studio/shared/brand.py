# demo-studio/shared/brand.py
"""Single source for the brand system.

Colour and type live in brand.json. Generators ask for a surface's tokens and
render them into a CSS :root block, so changing one hex changes every artifact.
Stdlib only, Python 3.9 compatible.
"""
import json
import os

_HERE = os.path.dirname(os.path.realpath(__file__))
_PATH = os.path.join(_HERE, "brand.json")

_cache = None


def _copy_dict(d):
    """Recursively copy a dict of dicts. Every leaf in brand.json is an
    immutable string, so only the dict nodes themselves need copying."""
    return {k: (_copy_dict(v) if isinstance(v, dict) else v) for k, v in d.items()}


def load():
    """Parse brand.json once, memoise it, and return a copy.

    Handing back the live cache would let any caller that mutates the
    returned dict poison it process-wide, for every subsequent caller. tokens()
    and root_block() already build a fresh dict on every call; load() must give
    the same guarantee to a caller that reaches for the raw data directly.
    """
    global _cache
    if _cache is None:
        with open(_PATH) as f:
            _cache = json.load(f)
    return _copy_dict(_cache)


def tokens(surface):
    """Ordered token map for a surface: core first, then that surface's own.

    Raises KeyError for an unknown surface, so a typo fails loudly rather than
    silently rendering an unstyled page.
    """
    data = load()
    surfaces = data["surfaces"]
    if surface not in surfaces:
        raise KeyError(
            "unknown surface %r, expected one of %s"
            % (surface, ", ".join(sorted(surfaces)))
        )
    merged = dict(data["core"])
    merged.update(surfaces[surface])
    return merged


def root_block(surface, indent="  ", sep="\n"):
    """The CSS :root{...} declaration for a surface."""
    lines = [
        "%s--%s:%s;" % (indent, name, value)
        for name, value in tokens(surface).items()
    ]
    return ":root{" + sep + sep.join(lines) + sep + "}"

