"""
data/

The data layer: DataFeed abstraction, validator, and the concrete
YahooFinanceFeed provider. yfinance is imported only inside
yfinance_feed.py -- nothing else in this package (or the project) touches
it directly.
"""

from data.base import DataFeed
from data.yfinance_feed import YahooFinanceFeed

__all__ = ["DataFeed", "YahooFinanceFeed"]