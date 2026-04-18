"""Year-over-year change and its historical percentile.

Useful for narration: "this is the strongest YoY increase since 2011".
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class YoYResult:
    last_yoy_pct: float
    percentile: float  # 0-100 among historical YoY changes


def yoy_change(values: list[float], *, period: int, history_years: int = 10) -> YoYResult | None:
    """Compute YoY change for the last point and its percentile rank.

    Percentile is the share of historical YoY changes *weaker in magnitude*
    than the current one — 95 means "stronger than 95% of past YoY moves".
    """
    if len(values) < period + 1:
        return None

    arr = np.asarray(values, dtype=float)

    yoy = (arr[period:] - arr[:-period]) / arr[:-period] * 100.0
    if len(yoy) < 4:
        return None

    last_yoy = float(yoy[-1])
    window = yoy[-(period * history_years):-1]
    if len(window) == 0:
        window = yoy[:-1]

    rank = float(np.mean(np.abs(window) < abs(last_yoy))) * 100.0
    return YoYResult(last_yoy_pct=last_yoy, percentile=rank)


def mom_change(values: list[float]) -> float | None:
    if len(values) < 2 or values[-2] == 0:
        return None
    return (values[-1] - values[-2]) / values[-2] * 100.0
