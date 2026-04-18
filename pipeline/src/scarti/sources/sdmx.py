"""Generic SDMX-JSON v1 client shared between ISTAT and Banca d'Italia."""
from __future__ import annotations

import asyncio
import time
from datetime import date
from typing import Any

import httpx

from scarti.sources.base import Observation


class RateLimiter:
    """Single-process async rate limiter — one slot, enforced minimum interval."""

    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            wait = self._min_interval - (time.monotonic() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


class SDMXClient:
    """Thin SDMX-JSON client. Subclasses only need to set base_url and agency."""

    def __init__(
        self,
        *,
        base_url: str,
        agency: str,
        min_interval: float,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(90.0, connect=10.0),
            headers={"Accept": "application/vnd.sdmx.data+json;version=1.0.0-wd"},
        )
        self._owns_client = client is None
        self._agency = agency
        self._limiter = RateLimiter(min_interval)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_dataflows(self) -> list[dict[str, Any]]:
        await self._limiter.acquire()
        r = await self._client.get(
            f"/dataflow/{self._agency}",
            headers={"Accept": "application/vnd.sdmx.structure+json;version=1.0.0-wd"},
            params={"detail": "allstubs"},
        )
        r.raise_for_status()
        flows = r.json().get("data", {}).get("dataflows", [])
        return [
            {
                "id": f.get("id"),
                "name": _pick_name(f.get("names", {})),
                "version": f.get("version"),
            }
            for f in flows
        ]

    async def fetch_observations(
        self,
        dataflow: str,
        key: str,
        *,
        start_period: str,
        extra_params: dict[str, str] | None = None,
    ) -> list[Observation]:
        params = {"startPeriod": start_period, "format": "jsondata"}
        if extra_params:
            params.update(extra_params)

        await self._limiter.acquire()
        r = await self._client.get(f"/data/{dataflow}/{key}", params=params)
        r.raise_for_status()
        return parse_sdmx_json(_loose_json(r.text))


def _pick_name(names: dict[str, str]) -> str:
    return names.get("it") or names.get("en") or next(iter(names.values()), "")


def start_period_for(frequency: str, months: int) -> str:
    today = date.today()
    if frequency == "M":
        year = today.year - (months // 12) - 1
        return f"{year}-01"
    if frequency == "Q":
        year = today.year - (months // 12) - 1
        return f"{year}-Q1"
    return str(today.year - (months // 12) - 1)


def drop_future(obs: list[Observation], frequency: str) -> list[Observation]:
    today = date.today()
    cutoff = today.strftime("%Y-%m") if frequency == "M" else str(today.year)
    return [o for o in obs if o.period <= cutoff]


def _loose_json(text: str) -> dict[str, Any]:
    """Decode SDMX-JSON resiliently. ISTAT sometimes appends a stray
    `"errors":[]` after the closing brace, which strict json.loads rejects.
    raw_decode parses the first valid object and silently drops the rest.
    """
    import json as _json

    return _json.JSONDecoder().raw_decode(text)[0]


def parse_sdmx_json(payload: dict[str, Any]) -> list[Observation]:
    # Two shapes exist in the wild:
    #   1.0 (original):  {"dataSets": [...], "structure": {...}, "meta": {...}}
    #   1.0 (ISTAT):     {"meta": {...}, "data": {"dataSets": [...], "structure": {...}}, "errors": []}
    if "data" in payload and "dataSets" in payload.get("data", {}):
        data_sets = payload["data"]["dataSets"]
        structure = payload["data"]["structure"]
    elif "dataSets" in payload:
        data_sets = payload["dataSets"]
        structure = payload["structure"]
    else:
        raise ValueError("Unexpected SDMX-JSON shape: no dataSets found")

    if not data_sets:
        return []

    time_values = _extract_time_values(structure)
    series_map = data_sets[0].get("series", {})

    if not series_map:
        raw_obs = data_sets[0].get("observations", {})
        return _flat(raw_obs, time_values)

    out: list[Observation] = []
    for _key, series_body in series_map.items():
        for time_idx, values in series_body.get("observations", {}).items():
            out.append(
                Observation(
                    period=time_values[int(time_idx)],
                    value=values[0] if values else None,
                )
            )
    out.sort(key=lambda o: o.period)
    return out


def _extract_time_values(structure: dict[str, Any]) -> list[str]:
    dims = structure.get("dimensions", {}).get("observation", [])
    for d in dims:
        if d.get("id") == "TIME_PERIOD":
            return [v["id"] for v in d.get("values", [])]
    raise ValueError("No TIME_PERIOD dimension in SDMX response")


def _flat(raw: dict[str, list[Any]], time_values: list[str]) -> list[Observation]:
    out = [
        Observation(period=time_values[int(idx)], value=(vals[0] if vals else None))
        for idx, vals in raw.items()
    ]
    out.sort(key=lambda o: o.period)
    return out
