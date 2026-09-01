"""
data/base.py

Defines the DataFeed abstraction: the single contract every historical
market data provider must satisfy.

No provider-specific imports belong in this file. This module must never
import yfinance, requests, or any networking/HTTP library.
"""

from abc import ABC, abstractmethod

import pandas as pd


class DataFeed(ABC):
    """
    Abstract base class for all historical market data providers.

    Any concrete implementation (YahooFinanceFeed, AlphaVantageFeed, a CSV
    file feed, a fake feed for tests, etc.) must implement `get_data` and
    return a DataFrame that already conforms to QuantBacktest's standardized
    OHLCV schema:

        index   -> pd.DatetimeIndex, sorted ascending, unique, tz-naive
        open    -> float64
        high    -> float64
        low     -> float64
        close   -> float64
        volume  -> int64

    Implementations are responsible for passing their raw provider output
    through `data.validator.validate_ohlcv` (or equivalent validation)
    before returning it. Callers of `get_data` should be able to trust the
    output unconditionally -- they should never need to re-validate it or
    know anything about where the data came from.
    """

    @abstractmethod
    def get_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """
        Fetch and return validated historical OHLCV data for one symbol.

        Args:
            symbol: Ticker symbol to fetch (e.g. "AAPL").
            start: Start date, inclusive, as an ISO string ("YYYY-MM-DD").
            end: End date, as an ISO string ("YYYY-MM-DD").

        Returns:
            A pandas DataFrame in the standardized OHLCV schema described
            in this class's docstring. The returned DataFrame must already
            be validated and cleaned -- callers must not need to validate
            it again.
        """
        raise NotImplementedError