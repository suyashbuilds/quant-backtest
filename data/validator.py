"""
data/validator.py

Validates and cleans a raw OHLCV DataFrame into QuantBacktest's
standardized schema, per Section 6 of the project context document.

This module has no knowledge of any specific data provider. It only knows
about the shape a DataFrame must have after cleaning.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataValidationError(ValueError):
    """Raised when a DataFrame cannot be brought into the standard OHLCV
    schema (e.g. a required column is missing entirely)."""


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean a raw OHLCV DataFrame into the standardized schema.

    Standardized schema (see Section 6 of the project context):
        index   -> DatetimeIndex, sorted ascending, unique, tz-naive
        open, high, low, close -> float64
        volume  -> int64, >= 0

    Rules applied, in order:
        1. Required columns must be present (open, high, low, close, volume).
        2. OHLC columns are coerced to numeric; values that cannot be
           interpreted as numbers become NaN.
        3. Rows with NaN in open/high/low/close are dropped (never
           forward-filled). A warning is logged with the count.
        4. NaN volume is treated as 0 (rows are NOT dropped for this).
        5. OHLC sanity is enforced: high >= max(open, close),
           low <= min(open, close), high >= low. Rows that violate this
           are dropped, never "repaired".
        6. Volume must be >= 0; rows with negative volume are dropped.
        7. The index is converted to a tz-naive DatetimeIndex.
        8. Duplicate timestamps are dropped, keeping the first occurrence.
        9. The index is sorted ascending.

    Args:
        df: Raw OHLCV DataFrame. Must have a DatetimeIndex (or an index
            convertible to one) and the required columns.

    Returns:
        A cleaned DataFrame with exactly the standardized schema.

    Raises:
        DataValidationError: if a required column is missing, or if the
            index cannot be interpreted as datetimes.
    """
    _check_required_columns(df)

    cleaned = df.copy()

    cleaned = _normalize_index(cleaned)
    cleaned = _coerce_numeric(cleaned)
    cleaned = _apply_nan_policy(cleaned)
    cleaned = _apply_ohlc_sanity(cleaned)
    cleaned = _apply_volume_policy(cleaned)
    cleaned = _drop_duplicate_timestamps(cleaned)
    cleaned = cleaned.sort_index()

    return cleaned[REQUIRED_COLUMNS]


def _check_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"Missing required column(s): {missing}. "
            f"A valid OHLCV DataFrame must contain: {REQUIRED_COLUMNS}"
        )


def _normalize_index(df: pd.DataFrame) -> pd.DataFrame:
    """Convert the index to a tz-naive DatetimeIndex."""
    try:
        index = pd.to_datetime(df.index)
    except Exception as exc:  # pragma: no cover - defensive
        raise DataValidationError(
            f"Index could not be converted to datetimes: {exc}"
        ) from exc

    if isinstance(index, pd.DatetimeIndex) and index.tz is not None:
        # Timezone policy (Section 6): daily bars are treated as tz-naive
        # exchange-local dates. Strip tz info at ingestion.
        index = index.tz_localize(None)

    df = df.copy()
    df.index = index
    return df


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Force OHLCV columns to numeric dtype; unparsable values become NaN."""
    df = df.copy()
    for col in REQUIRED_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _apply_nan_policy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows with NaN in open/high/low/close (never forward-fill).
    NaN volume is filled with 0 rather than dropping the row.
    """
    price_cols = ["open", "high", "low", "close"]
    nan_price_mask = df[price_cols].isna().any(axis=1)
    dropped = int(nan_price_mask.sum())
    if dropped:
        dropped_dates = df.index[nan_price_mask]
        logger.warning(
            "Dropped %d row(s) with NaN in open/high/low/close "
            "(date range of dropped rows: %s to %s)",
            dropped,
            dropped_dates.min(),
            dropped_dates.max(),
        )
    df = df.loc[~nan_price_mask].copy()

    nan_volume_mask = df["volume"].isna()
    if nan_volume_mask.any():
        logger.warning(
            "Filled %d row(s) with NaN volume as 0", int(nan_volume_mask.sum())
        )
        df.loc[nan_volume_mask, "volume"] = 0

    return df


def _apply_ohlc_sanity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reject (drop) rows that violate basic OHLC sanity:
        high >= max(open, close)
        low  <= min(open, close)
        high >= low
    Invalid rows are dropped, never silently repaired.
    """
    if df.empty:
        return df

    valid = (
        (df["high"] >= df[["open", "close"]].max(axis=1))
        & (df["low"] <= df[["open", "close"]].min(axis=1))
        & (df["high"] >= df["low"])
    )
    invalid_count = int((~valid).sum())
    if invalid_count:
        logger.warning(
            "Dropped %d row(s) failing OHLC sanity checks "
            "(high>=max(open,close), low<=min(open,close), high>=low)",
            invalid_count,
        )
    return df.loc[valid].copy()


def _apply_volume_policy(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with negative volume; cast volume to int64."""
    if df.empty:
        df["volume"] = df["volume"].astype("int64")
        return df

    valid = df["volume"] >= 0
    invalid_count = int((~valid).sum())
    if invalid_count:
        logger.warning("Dropped %d row(s) with negative volume", invalid_count)
    df = df.loc[valid].copy()
    df["volume"] = df["volume"].astype("int64")
    return df


def _drop_duplicate_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate index timestamps, keeping the first occurrence."""
    dup_mask = df.index.duplicated(keep="first")
    dup_count = int(dup_mask.sum())
    if dup_count:
        logger.warning(
            "Dropped %d duplicate timestamp row(s), keeping first occurrence",
            dup_count,
        )
    return df.loc[~dup_mask].copy()