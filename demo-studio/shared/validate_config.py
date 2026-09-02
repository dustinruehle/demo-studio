"""A very small schema walker.

Deliberately not jsonschema: the skill must run with no pip install. This covers
the shapes the Demo Studio configs actually use and reports every problem with a
dotted path, so an author can go straight to the field.
"""
import json


class ConfigError(Exception):
    """Raised when a config does not satisfy its schema."""


def load_config(path):
    """Load a JSON config file. A missing path or invalid JSON becomes a
    ConfigError naming the path, the same clean-message contract `enforce`
    gives every other config problem, rather than a raw traceback reaching
    the caller's terminal.
    """
    try:
        with open(path) as f:
            text = f.read()
    except OSError as err:
        raise ConfigError("could not read %s (%s)" % (path, err.strerror or err))
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise ConfigError("%s is not valid JSON (%s)" % (path, err))


_TYPE_NAMES = {
    "object": dict,
    "array": (list, tuple),
    "string": str,
    "number": (int, float),
    "boolean": bool,
}


def _type_name(value):
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if value is None:
        return "null"
    return type(value).__name__


def _matches(value, expected):
    names = (expected,) if isinstance(expected, str) else tuple(expected)
    for name in names:
        wanted = _TYPE_NAMES.get(name)
        if wanted is None:
            continue
        # bool is a subclass of int; keep them distinct
        if name == "number" and isinstance(value, bool):
            continue
        if isinstance(value, wanted):
            return True
    return False


def _walk(value, schema, path, name, errors):
    def fail(message):
        where = path or "<root>"
        errors.append("%s: %s: %s" % (name, where, message))

    expected = schema.get("type")
    if expected is not None and not _matches(value, expected):
        want = expected if isinstance(expected, str) else " or ".join(expected)
        fail("expected %s, got %s" % (want, _type_name(value)))
        return  # structure is wrong, deeper checks would be noise

    if "enum" in schema and value not in schema["enum"]:
        fail("expected one of %s, got %r"
             % (", ".join(repr(v) for v in schema["enum"]), value))

    if isinstance(value, str) and "minLength" in schema:
        if len(value) < schema["minLength"]:
            fail("must be at least %d character(s)" % schema["minLength"])

    if isinstance(value, dict):
        for key in schema.get("required", ()):
            if key not in value:
                child = key if not path else "%s.%s" % (path, key)
                errors.append("%s: %s: required field missing" % (name, child))
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                child = key if not path else "%s.%s" % (path, key)
                _walk(value[key], sub, child, name, errors)

    elif isinstance(value, (list, tuple)) and "items" in schema:
        for i, item in enumerate(value):
            _walk(item, schema["items"], "%s[%d]" % (path, i), name, errors)


def validate(config, schema, name="config"):
    """Return a list of human-readable errors, empty when the config is valid."""
    errors = []
    _walk(config, schema, "", name, errors)
    return errors


def enforce(config, schema, name="config"):
    """Raise ConfigError listing every problem. Call before building anything."""
    errors = validate(config, schema, name)
    if errors:
        raise ConfigError("%d config error(s):\n%s" % (len(errors), "\n".join(errors)))
