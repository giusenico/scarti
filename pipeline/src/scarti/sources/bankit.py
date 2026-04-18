from __future__ import annotations

import os

import httpx

from scarti.sources.base import Series, SeriesData, Source
from scarti.sources.sdmx import SDMXClient, drop_future, start_period_for

# Banca d'Italia SDMX endpoint. The official public endpoint has shifted in
# recent years; the env var lets you override without touching code.
#   - Historical: https://sdmx.bancaditalia.it/api/v1
#   - Some docs reference: https://sdmx.bancaditalia.it/SDMXWS/rest
# Verify the base URL from https://www.bancaditalia.it/statistiche/accesso-dati/
# before the first run and set SCARTI_BANKIT_BASE_URL.
DEFAULT_BASE_URL = "https://sdmx.bancaditalia.it/SDMXWS/rest"
AGENCY = "BIS"  # override per-series via SDMX key if needed
MIN_INTERVAL_SECONDS = 1.0


class BankITSource(Source):
    name = "bankit"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        agency: str | None = None,
        min_interval: float = MIN_INTERVAL_SECONDS,
    ) -> None:
        self._sdmx = SDMXClient(
            base_url=base_url or os.getenv("SCARTI_BANKIT_BASE_URL", DEFAULT_BASE_URL),
            agency=agency or os.getenv("SCARTI_BANKIT_AGENCY", AGENCY),
            min_interval=min_interval,
            client=client,
        )

    async def aclose(self) -> None:
        await self._sdmx.aclose()

    async def __aenter__(self) -> BankITSource:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def list_dataflows(self) -> list[dict]:
        return await self._sdmx.list_dataflows()

    async def fetch(self, series: Series, *, months: int = 120) -> SeriesData:
        if not series.is_ready:
            raise ValueError(f"Series {series.id} has placeholder SDMX codes (TODO)")

        start = start_period_for(series.frequency, months)
        obs = await self._sdmx.fetch_observations(
            series.sdmx_dataflow, series.sdmx_key, start_period=start
        )
        obs = drop_future(obs, series.frequency)
        return SeriesData(series=series, observations=obs)
