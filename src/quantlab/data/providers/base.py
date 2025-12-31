from __future__ import annotations

from datetime import date
from typing import Protocol, Sequence

import pandas as pd


class EodProvider(Protocol):
    """Provider protocol for fetching daily end-of-day market data."""

    name: str

    def fetch_eod(
        self,
        provider_symbols: Sequence[str],
        start: date,
        end: date,
        fields: Sequence[str],
    ) -> pd.DataFrame:
        """Return a DataFrame indexed by date with columns (provider_symbol, field)."""


__all__ = ["EodProvider"]
