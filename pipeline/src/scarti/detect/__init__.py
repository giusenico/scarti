"""Anomaly detection: stratified approach.

Strategy:
1. Prefer modified z-score on STL residual (handles trend + seasonality + outliers).
2. Fallback to modified z-score on raw values when STL isn't feasible
   (series too short, non-periodic).
3. Always compute YoY change and its percentile against the last 10y of YoYs
   for narrative use, even if not the primary detection method.
"""
from __future__ import annotations

from scarti.detect.detector import detect_anomaly, detect_all

__all__ = ["detect_anomaly", "detect_all"]
