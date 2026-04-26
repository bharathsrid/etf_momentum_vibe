"""Portfolio tracker for a single index — tracks position, cash, and equity curve."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Trade:
    """Record of a single trade execution."""
    date: pd.Timestamp    # execution date
    action: str           # "BUY" or "SELL"
    price: float          # execution price (T+1 open)
    shares: float         # number of shares traded
    value: float          # price * shares


class Portfolio:
    """Track position state and equity for a single index.

    The portfolio is either 100% invested (holding shares) or 100% in cash.
    Cash earns a daily risk-free rate.
    """

    def __init__(self, ticker: str, initial_cash: float, risk_free_rate: float = 0.02):
        self.ticker = ticker
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.shares = 0.0
        self.risk_free_rate = risk_free_rate
        self.trades: list[Trade] = []

        # Equity curve: list of (date, equity) tuples, converted to Series at end
        self._equity_records: list[tuple[pd.Timestamp, float]] = []

    @property
    def is_invested(self) -> bool:
        """Whether currently holding shares."""
        return self.shares > 0

    def go_long(self, price: float, date: pd.Timestamp) -> None:
        """Buy with all available cash at given price. No-op if already long."""
        if self.is_invested or self.cash <= 0:
            return

        self.shares = self.cash / price
        trade_value = self.cash
        self.cash = 0.0
        self.trades.append(Trade(
            date=date,
            action="BUY",
            price=price,
            shares=self.shares,
            value=trade_value,
        ))

    def go_cash(self, price: float, date: pd.Timestamp) -> None:
        """Sell all shares at given price. No-op if already in cash."""
        if not self.is_invested:
            return

        trade_value = self.shares * price
        self.cash = trade_value
        self.shares = 0.0
        self.trades.append(Trade(
            date=date,
            action="SELL",
            price=price,
            shares=0.0,
            value=trade_value,
        ))

    def mark_to_market(self, price: float, date: pd.Timestamp) -> None:
        """Record daily equity (cash + shares*price)."""
        equity = self.cash + self.shares * price
        self._equity_records.append((date, equity))

    def apply_daily_cash_interest(self) -> None:
        """Accrue risk-free rate on cash balance for one trading day."""
        if self.cash > 0:
            daily_rate = self.risk_free_rate / 252
            self.cash *= (1 + daily_rate)

    def get_equity_curve(self) -> pd.Series:
        """Return the equity curve as a pandas Series indexed by date."""
        if not self._equity_records:
            return pd.Series(dtype=float)
        dates, values = zip(*self._equity_records)
        return pd.Series(values, index=dates, name=self.ticker)
