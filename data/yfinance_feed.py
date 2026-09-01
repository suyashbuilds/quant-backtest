"""
data/yfinance_feed.py

The ONLY file in the entire project permitted to import yfinance.

Wraps yfinance.download(..., auto_adjust=True) and passes the result
through the shared validator before returning it. Everything downstream
of DataFeed only ever sees the standardized OHLCV schema -- it has no
idea yfinance exists.
"""

import pandas as pd
import yfinance as yf

from data.base import DataFeed
from data.validator import DataValidationError, validate_ohlcv


class YahooFinanceFeed(DataFeed):
    """DataFeed implementation backed by the yfinance library."""

    def get_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """
        Fetch daily OHLCV data for `symbol` between `start` and `end` from
        Yahoo Finance, using adjusted prices, and return it validated in
        the standardized OHLCV schema.

        Args:
            symbol: Ticker symbol (e.g. "AAPL").
            start: Start date, inclusive, "YYYY-MM-DD".
            end: End date, "YYYY-MM-DD".

        Returns:
            Validated, standardized OHLCV DataFrame.

        Raises:
            DataValidationError: if yfinance returns no data, or if the
                result cannot be brought into the standard schema.
        """
        raw = yf.download(
            symbol,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
        )

        if raw is None or raw.empty:
            raise DataValidationError(
                f"yfinance returned no data for symbol={symbol!r}, "
                f"start={start!r}, end={end!r}"
            )

        raw = self._flatten_columns(raw)
        raw = self._standardize_column_names(raw)

        return validate_ohlcv(raw)

    @staticmethod
    def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Modern yfinance versions may return a MultiIndex column structure
        (e.g. levels like ("Close", "AAPL")) even for a single symbol.
        For this single-symbol-per-backtest MVP, collapse that down to a
        flat column index by taking the first level (the OHLCV field name).
        """
        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            df.columns = df.columns.get_level_values(0)
        return df

    @staticmethod
    def _standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Map yfinance's Capitalized column names to the lowercase
        standard schema names."""
        rename_map = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df = df.rename(columns=rename_map)
        return df