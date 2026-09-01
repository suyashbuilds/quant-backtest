"""
tests/test_data.py

Tests for the data layer (data/base.py, data/validator.py).

These tests NEVER touch the network or yfinance. All test data is
constructed directly in-memory or as small deterministic fixtures.
"""

import pandas as pd
import pytest

from data.base import DataFeed
from data.validator import DataValidationError, validate_ohlcv


def make_valid_df(n=5, start="2024-01-01"):
    """Build a small, valid OHLCV DataFrame for use across tests."""
    dates = pd.date_range(start, periods=n, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0 + i for i in range(n)],
            "high": [101.0 + i for i in range(n)],
            "low": [99.0 + i for i in range(n)],
            "close": [100.5 + i for i in range(n)],
            "volume": [1000 + i for i in range(n)],
        },
        index=dates,
    )


def test_valid_data_passes_validation():
    df = make_valid_df()
    result = validate_ohlcv(df)
    assert list(result.columns) == ["open", "high", "low", "close", "volume"]
    assert len(result) == len(df)
    assert isinstance(result.index, pd.DatetimeIndex)


def test_missing_required_column_raises():
    df = make_valid_df().drop(columns=["volume"])
    with pytest.raises(DataValidationError):
        validate_ohlcv(df)


def test_nan_close_row_is_dropped(caplog):
    df = make_valid_df(n=5)
    df.iloc[2, df.columns.get_loc("close")] = float("nan")
    with caplog.at_level("WARNING"):
        result = validate_ohlcv(df)
    assert len(result) == 4
    assert df.index[2] not in result.index
    assert result["close"].isna().sum() == 0
    assert any("Dropped" in msg for msg in caplog.messages)


def test_nan_volume_becomes_zero_row_kept():
    df = make_valid_df(n=5)
    df.iloc[1, df.columns.get_loc("volume")] = float("nan")
    result = validate_ohlcv(df)
    assert len(result) == 5
    assert result.iloc[1]["volume"] == 0
    assert result["volume"].dtype == "int64"


def test_duplicate_timestamps_keeps_first():
    df = make_valid_df(n=3)
    dup_row = df.iloc[[0]].copy()
    dup_row["close"] = 999.0
    df_with_dup = pd.concat([df, dup_row])
    result = validate_ohlcv(df_with_dup)
    assert len(result) == 3
    assert not result.index.duplicated().any()
    assert result.loc[df.index[0], "close"] != 999.0


def test_unsorted_timestamps_are_sorted():
    df = make_valid_df(n=4)
    shuffled = df.iloc[[2, 0, 3, 1]]
    result = validate_ohlcv(shuffled)
    assert list(result.index) == sorted(result.index)


def test_timezone_aware_index_becomes_naive():
    df = make_valid_df(n=3)
    df.index = df.index.tz_localize("US/Eastern")
    result = validate_ohlcv(df)
    assert result.index.tz is None


def test_invalid_ohlc_row_is_dropped():
    df = make_valid_df(n=3)
    df.iloc[1, df.columns.get_loc("open")] = 100.0
    df.iloc[1, df.columns.get_loc("high")] = 90.0
    df.iloc[1, df.columns.get_loc("low")] = 95.0
    df.iloc[1, df.columns.get_loc("close")] = 100.0
    result = validate_ohlcv(df)
    assert len(result) == 2
    assert df.index[1] not in result.index


def test_negative_volume_row_is_dropped():
    df = make_valid_df(n=3)
    df.iloc[0, df.columns.get_loc("volume")] = -100
    result = validate_ohlcv(df)
    assert len(result) == 2
    assert df.index[0] not in result.index


def test_final_schema_is_exact():
    df = make_valid_df()
    result = validate_ohlcv(df)
    assert list(result.columns) == ["open", "high", "low", "close", "volume"]
    assert result["open"].dtype == "float64"
    assert result["high"].dtype == "float64"
    assert result["low"].dtype == "float64"
    assert result["close"].dtype == "float64"
    assert result["volume"].dtype == "int64"
    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.index.tz is None
    assert result.index.is_monotonic_increasing
    assert not result.index.duplicated().any()


class FakeDataFeed(DataFeed):
    """A trivial in-memory DataFeed used only to prove that the engine
    (later, in M5) can depend on the DataFeed abstraction rather than on
    any specific provider like YahooFinanceFeed."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def get_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        return validate_ohlcv(self._df)


def test_datafeed_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        DataFeed()


def test_fake_datafeed_satisfies_the_interface():
    df = make_valid_df()
    feed: DataFeed = FakeDataFeed(df)
    result = feed.get_data("FAKE", "2024-01-01", "2024-01-05")
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["open", "high", "low", "close", "volume"]