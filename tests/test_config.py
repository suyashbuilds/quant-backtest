"""
tests/test_config.py

Tests for config.settings.BacktestConfig.
"""

import pytest

from config import BacktestConfig


def test_valid_config_is_created():
    """A config with sensible values should construct without error
    and store exactly the values passed in."""
    config = BacktestConfig(
        symbol="AAPL",
        start_date="2020-01-01",
        end_date="2023-01-01",
        initial_capital=50_000.0,
        commission_pct=0.002,
        slippage_pct=0.001,
    )
    assert config.symbol == "AAPL"
    assert config.start_date == "2020-01-01"
    assert config.end_date == "2023-01-01"
    assert config.initial_capital == 50_000.0
    assert config.commission_pct == 0.002
    assert config.slippage_pct == 0.001


def test_default_values_are_applied():
    """Omitting the optional fields should fall back to the spec's
    documented defaults."""
    config = BacktestConfig(
        symbol="MSFT",
        start_date="2021-01-01",
        end_date="2022-01-01",
    )
    assert config.initial_capital == 100_000.0
    assert config.commission_pct == 0.001
    assert config.slippage_pct == 0.0005


def test_invalid_initial_capital_is_rejected():
    """initial_capital <= 0 makes no economic sense for a backtest
    and must be rejected at construction time."""
    with pytest.raises(ValueError):
        BacktestConfig(
            symbol="AAPL",
            start_date="2020-01-01",
            end_date="2023-01-01",
            initial_capital=0,
        )


def test_negative_commission_is_rejected():
    """A negative commission would mean the broker pays you to trade —
    not a real scenario, must be rejected."""
    with pytest.raises(ValueError):
        BacktestConfig(
            symbol="AAPL",
            start_date="2020-01-01",
            end_date="2023-01-01",
            commission_pct=-0.001,
        )


def test_negative_slippage_is_rejected():
    """A negative slippage would mean fills are always favorable to the
    trader, which contradicts Section 8's adverse-slippage model."""
    with pytest.raises(ValueError):
        BacktestConfig(
            symbol="AAPL",
            start_date="2020-01-01",
            end_date="2023-01-01",
            slippage_pct=-0.0005,
        )