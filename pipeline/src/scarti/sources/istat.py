from __future__ import annotations

import httpx

from scarti.sources.base import Series, SeriesData, Source
from scarti.sources.sdmx import SDMXClient, drop_future, start_period_for

BASE_URL = "https://esploradati.istat.it/SDMXWS/rest"
AGENCY = "IT1"
MIN_INTERVAL_SECONDS = 13.0  # ~5 req/min documented — leave margin


class ISTATSource(Source):
    name = "istat"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        min_interval: float = MIN_INTERVAL_SECONDS,
    ) -> None:
        self._sdmx = SDMXClient(
            base_url=BASE_URL,
            agency=AGENCY,
            min_interval=min_interval,
            client=client,
        )

    async def aclose(self) -> None:
        await self._sdmx.aclose()

    async def __aenter__(self) -> ISTATSource:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def list_dataflows(self) -> list[dict]:
        return await self._sdmx.list_dataflows()

    async def fetch(self, series: Series, *, months: int = 120) -> SeriesData:
        if not series.is_ready:
            raise ValueError(f"Series {series.id} has placeholder SDMX codes (TODO)")

        start = start_period_for(series.frequency, months)
        # Known ISTAT bug: endPeriod=N returns up to N+1. We deliberately do
        # NOT set endPeriod and trim future periods client-side instead.
        obs = await self._sdmx.fetch_observations(
            series.sdmx_dataflow, series.sdmx_key, start_period=start
        )
        obs = drop_future(obs, series.frequency)
        return SeriesData(series=series, observations=obs)
