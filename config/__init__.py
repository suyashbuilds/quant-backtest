"""
config package

Exposes BacktestConfig so callers can write:
    from config import BacktestConfig
instead of:
    from config.settings import BacktestConfig
"""

from config.settings import BacktestConfig

__all__ = ["BacktestConfig"]