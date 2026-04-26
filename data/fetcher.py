"""Data fetching and caching module for Yahoo Finance EOD data."""

import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


def fetch_all(
    tickers: dict[str, str],
    start: str,
    end: str | None = None,
    cache_dir: str = "data/cache",
) -> dict[str, pd.DataFrame]:
    """Download and cache data for all tickers.

    Args:
        tickers: Mapping of ticker symbol to friendly name.
        start: Start date string (YYYY-MM-DD).
        end: End date string (YYYY-MM-DD). None means today.
        cache_dir: Directory for Parquet cache files.

    Returns:
        Dict mapping ticker symbol to DataFrame with OHLCV columns and DatetimeIndex.
    """
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")

    os.makedirs(cache_dir, exist_ok=True)

    result = {}
    for ticker, name in tickers.items():
        print(f"  Fetching {name} ({ticker})...", end=" ")
        df = _load_cache(ticker, cache_dir, end)
        if df is not None:
            print(f"cached ({len(df)} bars)")
        else:
            df = _fetch_single(ticker, start, end)
            _save_cache(ticker, df, cache_dir)
            print(f"downloaded ({len(df)} bars)")

        if df is not None and len(df) > 0:
            result[ticker] = df
        else:
            print(f"  WARNING: No data for {ticker}")

    return result


def _fetch_single(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download one ticker from Yahoo Finance.

    Returns DataFrame with columns: Open, High, Low, Close, Volume
    and a DatetimeIndex (timezone-naive).
    """
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    if df.empty:
        return df

    # Handle MultiIndex columns (yfinance >= 0.2.37 returns them for single tickers)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Keep only OHLCV
    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[cols]

    # Make timezone-naive
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    # Forward-fill any NaNs, then drop remaining
    df = df.ffill().dropna()

    return df


def _load_cache(ticker: str, cache_dir: str, end_date: str) -> pd.DataFrame | None:
    """Load from Parquet cache if it exists and is fresh (<1 day old)."""
    safe_ticker = ticker.replace("^", "IDX_").replace(".", "_")
    path = os.path.join(cache_dir, f"{safe_ticker}.parquet")

    if not os.path.exists(path):
        return None

    # Check if cache is fresh (less than 1 day old)
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    if datetime.now() - mtime > timedelta(days=1):
        return None

    # Check if cached data covers the end date
    df = pd.read_parquet(path)
    if df.empty:
        return None

    last_date = df.index[-1]
    if isinstance(last_date, pd.Timestamp):
        last_date_str = last_date.strftime("%Y-%m-%d")
        # If cached data ends more than 2 days before requested end, stale
        if last_date_str < end_date:
            end_dt = pd.Timestamp(end_date)
            if (end_dt - last_date).days > 2:
                return None

    return df


def _save_cache(ticker: str, df: pd.DataFrame, cache_dir: str) -> None:
    """Save DataFrame to Parquet cache."""
    safe_ticker = ticker.replace("^", "IDX_").replace(".", "_")
    path = os.path.join(cache_dir, f"{safe_ticker}.parquet")
    df.to_parquet(path)
