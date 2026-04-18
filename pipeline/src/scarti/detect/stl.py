"""STL decomposition: separate trend, seasonal, residual — then z-score residual."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from scarti.detect.mod_zscore import MAD_CONSTANT


@dataclass(frozen=True)
class STLResult:
    value: float
    residual: float
    zscore: float
    residual_median: float
    residual_mad: float


def stl_mod_zscore(values: list[float], *, period: int) -> STLResult | None:
    """STL decompose the series, take the residual, and compute its modified z-score.

    `period` is the seasonal period in the sampling frequency:
      - 12 for monthly data with annual seasonality
      - 4 for quarterly data with annual seasonality

    Requires statsmodels. Returns None if the series is too short or MAD=0.
    """
    try:
        from statsmodels.tsa.seasonal import STL
    except ImportError:
        return None

    # STL needs ≥ 2 full cycles + a bit. 3 cycles is a safe minimum.
    if len(values) < period * 3:
        return None

    series = pd.Series(values, dtype=float)
    try:
        result = STL(series, period=period, robust=True).fit()
    except Exception:
        return None

    residual = np.asarray(result.resid.values, dtype=float)
    last_resid = float(residual[-1])

    prior = residual[:-1]
    median = float(np.median(prior))
    mad = float(np.median(np.abs(prior - median)))
    if mad == 0.0:
        return None

    zscore = MAD_CONSTANT * (last_resid - median) / mad
    return STLResult(
        value=float(values[-1]),
        residual=last_resid,
        zscore=zscore,
        residual_median=median,
        residual_mad=mad,
    )
