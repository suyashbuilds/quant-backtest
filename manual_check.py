from data.yfinance_feed import YahooFinanceFeed

feed = YahooFinanceFeed()
data = feed.get_data("AAPL", "2020-01-01", "2023-01-01")

print(data.head())
print(data.tail())
print(data.dtypes)
print(data.index)