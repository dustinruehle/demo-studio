# demo-studio/shared/guardrails.py
"""Mechanical enforcement of the Demo Studio guardrails.

The skill documents these as disciplines. Documented rules get forgotten under
pressure, so they are checked here and hard-fail the build. Stdlib only,
Python 3.9 compatible.
"""
import re
import sys
import zipfile
from collections import namedtuple

Violation = namedtuple("Violation", "check field detail")

EM_DASH = "\u2014"

# Filler that reads as machine-written. Engineer-to-engineer register is terse.
AI_TELLS = (
    "seamless", "robust", "leverage", "genuinely",
    "delve", "honestly", "actually",
)


class GuardrailError(Exception):
    """Raised when a build would ship a guardrail violation."""


def _word_re(word):
    # Lookarounds, not \b: \b requires a word/non-word transition, which can
    # never occur at a position where the term's own edge character is
    # already non-word (C++, Yahoo!, (x)). Lookarounds only check what is
    # adjacent to the match, not the match's own first/last character.
    return re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.IGNORECASE)


_TELL_RES = tuple((w, _word_re(w)) for w in AI_TELLS)


def check_text(value, field, allowlist=(), banned=()):
    """Check one string. Returns a list of Violation, empty when clean."""
    if not isinstance(value, str):
        return []
    out = []
    if EM_DASH in value:
        out.append(Violation("em-dash", field, "use a comma or restructure"))
    permitted = {w.lower() for w in allowlist}
    for word, pattern in _TELL_RES:
        if word in permitted:
            continue
        if pattern.search(value):
            out.append(Violation("ai-tell", field, word))
    for term in banned:
        if _word_re(term).search(value):
            out.append(Violation("public-safe", field, term))
    return out


_META_KEYS = ("banned_terms", "allow_words")


def check_tree(obj, allowlist=(), banned=(), _path=""):
    """Walk a config tree, checking every string value.

    Paths read like acts[0].cards[1].why so a failure points at the exact field
    the author has to edit.

    `banned_terms` and `allow_words` are skipped when they appear as dict keys.
    Both lists are read out of the same config they are walked against (a
    generator does `banned=cfg.get("banned_terms", ())` and then walks `cfg`
    itself), so without this skip a banned term flags itself the moment it is
    declared, and the escape list becomes unusable the moment anyone uses it.
    """
    out = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in _META_KEYS:
                continue
            child = key if not _path else "%s.%s" % (_path, key)
            out.extend(check_tree(value, allowlist, banned, child))
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            out.extend(check_tree(value, allowlist, banned, "%s[%d]" % (_path, i)))
    elif isinstance(obj, str):
        out.extend(check_text(obj, _path or "<root>", allowlist, banned))
    return out


def report(violations):
    """One violation per line, ordered as found."""
    return "\n".join(
        "  %-12s %-40s %s" % (v.check, v.field, v.detail) for v in violations
    )


def enforce(violations):
    """Raise if anything was found. Call this before writing any output file."""
    if violations:
        message = "%d guardrail violation(s):\n%s" % (len(violations), report(violations))
        if any(v.check == "ai-tell" for v in violations):
            message += (
                "\n  a legitimate technical use of a listed word can be permitted "
                "by adding it to allow_words in the config"
            )
        raise GuardrailError(message)


# Constructs Google Slides silently drops on import. A deck can look correct in
# PowerPoint and arrive in Slides with its arrows missing, so check the file.
_PPTX_BANNED = (
    ("pptx-connector", re.compile(r"<p:cxnSp[ >]"),
     "line connector, use a block arrow autoshape"),
    ("pptx-connector", re.compile(r'prst="(straight|bent|curved)Connector'),
     "connector geometry, use a block arrow autoshape"),
    ("pptx-dash", re.compile(r"<a:prstDash[ >]"),
     "dashed line, use a solid border"),
)


def check_pptx(path):
    """Scan a generated .pptx for constructs that do not survive Google Slides."""
    import os
    out = []
    try:
        with zipfile.ZipFile(path) as z:
            names = sorted(n for n in z.namelist()
                           if re.match(r"ppt/slides/slide\d+\.xml$", n))
            for name in names:
                slide = re.sub(r".*/(slide\d+)\.xml$", r"\1", name)
                xml = z.read(name).decode("utf-8", "replace")
                for check, pattern, detail in _PPTX_BANNED:
                    if pattern.search(xml):
                        out.append(Violation(check, slide, detail))
    except FileNotFoundError:
        out.append(Violation("pptx-unreadable", os.path.basename(path),
                            "file not found"))
    except zipfile.BadZipFile:
        out.append(Violation("pptx-unreadable", os.path.basename(path),
                            "not a valid zip file"))
    return out


if __name__ == "__main__":
    # The gate that cannot be bypassed by hand-editing a builder: this checks
    # the .pptx file that actually got written, not the code that wrote it.
    if len(sys.argv) != 2:
        sys.stderr.write("usage: guardrails.py DECK.pptx\n")
        sys.exit(1)
    found = check_pptx(sys.argv[1])
    if found:
        print(report(found))
        sys.exit(1)
    print("clean: no guardrail violations in %s" % sys.argv[1])
