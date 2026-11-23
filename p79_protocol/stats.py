"""Paired original-recording component bootstrap."""

from math import isfinite
from numbers import Integral


def paired_component_rates(first, second, draws):
    """Use the same ordered component indices for both sides of each draw."""
    if not len(first) or len(first) != len(second):
        raise ValueError("Both sides must describe the same ordered components")
    if any(not (isinstance(hits, Integral) and isinstance(total, Integral) and 0 <= hits <= total)
           for hits, total in (*first, *second)):
        raise ValueError("Invalid component counts")
    for indices in draws:
        if len(indices) != len(first) or any(not isinstance(i, Integral) or not 0 <= i < len(first) for i in indices):
            raise ValueError("Bad component draw")
        rates = []
        for side in (first, second):
            hits = sum(int(side[i][0]) for i in indices)
            total = sum(int(side[i][1]) for i in indices)
            rates.append(hits / total if total else float("nan"))
        yield (*rates, rates[1] - rates[0])


def historical_draws(n_components, seed, repeats=10_000):
    """Archived PCG64 draw order, optional NumPy dependency."""
    if not all(isinstance(n, Integral) and n > 0 for n in (n_components, repeats)):
        raise ValueError("Positive component and replicate counts required")
    import numpy as np

    return np.random.default_rng(seed).integers(0, n_components, (repeats, n_components))


def percentile_interval(values):
    """Linear 2.5/97.5 percentiles after dropping unestimable draws."""
    ordered = sorted(value for value in values if isfinite(value))
    if not ordered:
        return None

    def quantile(fraction):
        position = fraction * (len(ordered) - 1)
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] + weight * (ordered[upper] - ordered[lower])

    return quantile(0.025), quantile(0.975)
