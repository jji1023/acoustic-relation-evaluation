"""In-memory placement of normalized source prefixes, with no audio I/O."""

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from struct import pack, unpack


@dataclass(frozen=True)
class Recipe:
    early: float
    late: float
    short: float
    long: float
    contrast_db: float


RECIPES = {
    "R0": Recipe(2, 7, 0.5, 1, 12),
    "R1": Recipe(1, 6, 0.4, 0.9, 10),
    "C0": Recipe(2, 7, 0.5, 1, 12),
    "C1": Recipe(1.5, 6.5, 0.6, 1.1, 11),
}


def relation_roles(bits):
    if len(bits) != 3 or set(bits) - {"0", "1"}:
        raise ValueError("Expected a three-bit Position, Duration, Level key")
    return tuple("AB"[int(bit)] for bit in bits)


def crop(samples, start, length):
    if not isinstance(start, int) or not isinstance(length, int):
        raise ValueError("Crop bounds must be integers")
    if start < 0 or length <= 0 or start + length > len(samples):
        raise ValueError("Crop outside source")
    result = tuple(float(x) for x in samples[start:start + length])
    if not all(map(isfinite, result)):
        raise ValueError("Non-finite source samples")
    return result


def normalize(anchor, measured_active_rms_dbfs, reference_dbfs=-27.0):
    if not all(map(isfinite, (measured_active_rms_dbfs, reference_dbfs))):
        raise ValueError("Finite level inputs required")
    gain = reference_dbfs - measured_active_rms_dbfs
    try:
        multiplier = 10.0 ** (gain / 20.0)
    except OverflowError as exc:
        raise ValueError("Normalization gain is out of range") from exc
    result = tuple(float(x) * multiplier for x in anchor)
    if multiplier == 0.0 or not all(map(isfinite, result)):
        raise ValueError("Normalization would produce an invalid anchor")
    return result


def render(anchors, bits, recipe, *, sample_rate=44100, seconds=10, float32_mix=False):
    """Return scene samples and per-source placement. Anchors are already normalized."""
    if set(anchors) != {"A", "B"} or type(sample_rate) is not int or sample_rate <= 0:
        raise ValueError("Expected two role-keyed anchors and a positive integer sample rate")
    if not isfinite(seconds) or seconds <= 0:
        raise ValueError("Scene duration must be finite and positive")
    if not all(map(isfinite, (recipe.early, recipe.late, recipe.short, recipe.long, recipe.contrast_db))):
        raise ValueError("Recipe values must be finite")
    early, late, short, long = (round(value * sample_rate) for value in
                                (recipe.early, recipe.late, recipe.short, recipe.long))
    scene_samples = round(seconds * sample_rate)
    if not (0 <= early < late and 0 < short < long and recipe.contrast_db > 0):
        raise ValueError("Recipe requires distinct slots and crop lengths and positive level contrast")
    if early + long > late or late + long > scene_samples:
        raise ValueError("Recipe requires nonoverlapping crops inside the scene")
    first, longer, louder = relation_roles(bits)
    mixed = [0.0] * scene_samples
    placement = {}
    for role in ("A", "B"):
        start = early if role == first else late
        length = long if role == longer else short
        gain = recipe.contrast_db / 2 * (1 if role == louder else -1)
        prefix = crop(anchors[role], 0, length)
        try:
            multiplier = 10.0 ** (gain / 20)
        except OverflowError as exc:
            raise ValueError("Recipe gain is out of range") from exc
        for index, sample in enumerate(prefix, start):
            mixed[index] += multiplier * sample
        placement[role] = (start, length, gain)
    if any(not -1.0 < v < 1.0 for v in mixed):
        raise ValueError("Scene would clip or contains non-finite samples")
    if float32_mix:
        mixed = [unpack("<f", pack("<f", v))[0] for v in mixed]
        if any(abs(v) >= 1.0 for v in mixed):
            raise ValueError("Scene would clip after float32 conversion")
    return mixed, placement


def sample_digest(samples):
    """SHA-256 of little-endian float64 values, independent of any WAV header."""
    digest = sha256()
    for value in samples:
        digest.update(pack("<d", value))
    return digest.hexdigest()
