"""
config/settings.py

Defines BacktestConfig — the single object describing the parameters of
one backtest run (symbol, date range, capital, and trading costs).

BacktestConfig does NOT include the Strategy instance or its parameters.
The Strategy is constructed and passed to BacktestEngine separately —
see Section 14 of the project context for why this boundary is kept.
"""

from dataclasses import dataclass


@dataclass
class BacktestConfig:
    """
    Configuration for a single backtest run.

    Attributes:
        symbol: Ticker symbol to backtest, e.g. "AAPL".
        start_date: Start of the backtest window, e.g. "2020-01-01".
        end_date: End of the backtest window, e.g. "2023-01-01".
        initial_capital: Starting cash for the portfolio. Must be > 0.
        commission_pct: Commission as a fraction of trade notional
            (e.g. 0.001 = 0.1%). Must be >= 0.
        slippage_pct: Slippage as a fraction of price (e.g. 0.0005 = 0.05%).
            Must be >= 0.
    """

    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100_000.0
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005

    def __post_init__(self) -> None:
        """Reject obviously invalid numeric configuration values."""
        if self.initial_capital <= 0:
            raise ValueError(
                f"initial_capital must be > 0, got {self.initial_capital}"
            )
        if self.commission_pct < 0:
            raise ValueError(
                f"commission_pct must be >= 0, got {self.commission_pct}"
            )
        if self.slippage_pct < 0:
            raise ValueError(
                f"slippage_pct must be >= 0, got {self.slippage_pct}"
            )