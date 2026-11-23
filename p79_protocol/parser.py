"""Independent implementation of the archived parser behavior."""

import re
import unicodedata


_QUOTES = str.maketrans("‘’“”", "\x27\x27\x22\x22")
_PREFIX = re.compile(r"^(?:answer\s*[:\-]\s*|(?:the answer is|answer is|it is)\s+)")
_STRICT = re.compile(r"\s*([AaBb])\s*[.!]?\s*")


def _key(value):
    value = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    value = value.translate(_QUOTES)
    value = re.sub(r"""^[\s"'\x60]+|[\s"'\x60]+$""", "", value)
    return " ".join(value.rstrip(".!?;:,").split())


def sound_name_keys(names):
    if isinstance(names, str) or len(names) != 2 or any(not isinstance(name, str) for name in names):
        raise ValueError("Expected two sound names")
    keys = tuple(map(_key, names))
    if not all(keys) or keys[0] == keys[1]:
        raise ValueError("Sound names must be nonempty and distinct after normalization")
    return keys


def parse(raw, names, displayed_roles, interface):
    """Return semantic label, validity, and status for a text response or None."""
    option_keys = sound_name_keys(names)
    if tuple(displayed_roles) not in (("A", "B"), ("B", "A")):
        raise ValueError("Expected the AB or BA semantic role order")
    if raw is None:
        raw = ""
    if not isinstance(raw, str):
        raise ValueError("Expected a text response or None")
    if interface == "LETTER":
        match = _STRICT.fullmatch(raw)
        if match is None:
            return "INVALID", False, "invalid_or_ambiguous"
        index = 0 if match[1].upper() == "A" else 1
        return displayed_roles[index], True, f"VALID_DISPLAY_{index + 1}"
    if interface != "SOUND":
        raise ValueError("Unknown interface")
    lines = [line for line in raw.splitlines() if line.strip()]
    if not lines:
        return "INVALID", False, "empty"
    first = _key(lines[0])
    for candidate in (first, _PREFIX.sub("", first, count=1).strip()):
        if candidate in option_keys:
            index = option_keys.index(candidate)
            return displayed_roles[index], True, f"VALID_DISPLAY_{index + 1}"
    whole = _key(raw)
    found = [index for index, option in enumerate(option_keys)
             if re.search(r"(?<!\w)" + re.escape(option) + r"(?!\w)", whole)]
    if len(found) == 1:
        index = found[0]
        return displayed_roles[index], True, f"VALID_DISPLAY_{index + 1}_MENTION"
    return "INVALID", False, "invalid_or_ambiguous"
