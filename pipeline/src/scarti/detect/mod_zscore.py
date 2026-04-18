"""Modified z-score using median and MAD (median absolute deviation).

Robust to outliers. A value is "anomalous" if |mod_z| >= threshold.

    mod_z = 0.6745 * (x - median) / MAD     (Iglewicz & Hoaglin, 1993)

When scaled by 1/0.6745 ≈ 1.4826, MAD is a consistent estimator of sigma
under normality, so mod_z is comparable to a classical z-score.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MAD_CONSTANT = 0.6745


@dataclass(frozen=True)
class ModZScoreResult:
    value: float
    zscore: float
    median: float
    mad: float


def modified_zscore(values: list[float]) -> ModZScoreResult | None:
    """Compute modified z-score of the LAST value against the preceding ones.

    Returns None if not enough data or MAD is zero (degenerate series).
    """
    if len(values) < 12:
        return None

    arr = np.asarray(values[:-1], dtype=float)
    last = float(values[-1])

    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))

    if mad == 0.0:
        return None

    zscore = MAD_CONSTANT * (last - median) / mad
    return ModZScoreResult(value=last, zscore=zscore, median=median, mad=mad)
