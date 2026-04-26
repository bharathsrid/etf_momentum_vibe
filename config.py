"""Central configuration for the ETF Momentum Backtest project."""

# Ticker symbols mapped to friendly names
TICKERS = {
    "^GSPC": "S&P 500",
    "^FTSE": "FTSE 100",
    "^NSEI": "Nifty 50",
    "^STOXX50E": "STOXX 50",
}

START_DATE = "2016-01-01"
END_DATE = None  # None means "today" at runtime

INITIAL_CAPITAL = 10_000.0
CAPITAL_PER_INDEX = INITIAL_CAPITAL / len(TICKERS)  # 2500

RISK_FREE_RATE = 0.02  # 2% annualized

# Signal at T close → execute at T+1 open
CACHE_DIR = "data/cache"
OUTPUT_DIR = "output"
