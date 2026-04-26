"""Core backtest engine — orchestrates the backtest loop for a single (ticker, strategy) pair."""

from dataclasses import dataclass

import pandas as pd

from engine.portfolio import Portfolio, Trade
from strategies.base import Signal, Strategy


@dataclass
class BacktestResult:
    """Result of a single backtest run."""
    ticker: str
    strategy_name: str
    strategy_params: dict
    equity_curve: pd.Series
    trades: list[Trade]
    initial_cash: float
    final_equity: float


class BacktestEngine:
    """Run a backtest for one ticker with one strategy.

    Core loop:
    1. Generate signal from strategy using data up to day T close
    2. Execute trade at day T+1 open price (if signal changed)
    3. Mark to market at day T close
    4. Accrue interest on cash balance
    """

    def __init__(
        self,
        ticker: str,
        data: pd.DataFrame,
        strategy: Strategy,
        initial_cash: float,
        risk_free_rate: float = 0.02,
    ):
        self.ticker = ticker
        self.data = data
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.risk_free_rate = risk_free_rate

    def run(self) -> BacktestResult:
        """Execute the backtest and return results."""
        # Reset strategy state for fresh run
        self.strategy.reset()

        portfolio = Portfolio(
            ticker=self.ticker,
            initial_cash=self.initial_cash,
            risk_free_rate=self.risk_free_rate,
        )

        warmup = self.strategy.warmup
        n = len(self.data)

        # During warmup: portfolio stays in cash, but we still mark-to-market
        for i in range(min(warmup, n)):
            date = self.data.index[i]
            close = self.data["Close"].iloc[i]
            portfolio.mark_to_market(close, date)
            portfolio.apply_daily_cash_interest()

        # Main backtest loop: start generating signals after warmup
        for i in range(warmup, n):
            # 1. Generate signal using data up to and including day i
            signal = self.strategy.signal(self.data.iloc[: i + 1])

            # 2. Execute at T+1 open if signal changed
            if i + 1 < n:
                execution_price = self.data["Open"].iloc[i + 1]
                execution_date = self.data.index[i + 1]

                if signal == Signal.INVESTED and not portfolio.is_invested:
                    portfolio.go_long(execution_price, execution_date)
                elif signal == Signal.CASH and portfolio.is_invested:
                    portfolio.go_cash(execution_price, execution_date)

            # 3. Mark to market using today's close
            close = self.data["Close"].iloc[i]
            date = self.data.index[i]
            portfolio.mark_to_market(close, date)

            # 4. Accrue interest on cash
            portfolio.apply_daily_cash_interest()

        equity_curve = portfolio.get_equity_curve()
        final_equity = equity_curve.iloc[-1] if len(equity_curve) > 0 else self.initial_cash

        return BacktestResult(
            ticker=self.ticker,
            strategy_name=self.strategy.name,
            strategy_params=self.strategy.params,
            equity_curve=equity_curve,
            trades=portfolio.trades,
            initial_cash=self.initial_cash,
            final_equity=final_equity,
        )


def run_buy_and_hold(
    ticker: str,
    data: pd.DataFrame,
    initial_cash: float,
    risk_free_rate: float = 0.02,
    warmup: int = 0,
) -> BacktestResult:
    """Run a buy-and-hold benchmark for comparison.

    Buys at the open of the first trading day (after warmup) and holds to end.
    """
    portfolio = Portfolio(
        ticker=ticker,
        initial_cash=initial_cash,
        risk_free_rate=risk_free_rate,
    )

    # During warmup: stay in cash, mark to market
    for i in range(min(warmup, len(data))):
        date = data.index[i]
        close = data["Close"].iloc[i]
        portfolio.mark_to_market(close, date)
        portfolio.apply_daily_cash_interest()

    # Buy at open of first post-warmup day
    if warmup < len(data):
        buy_price = data["Open"].iloc[warmup]
        buy_date = data.index[warmup]
        portfolio.go_long(buy_price, buy_date)

    # Mark to market for remaining days
    for i in range(warmup, len(data)):
        close = data["Close"].iloc[i]
        date = data.index[i]

        # Execute buy at open of warmup day (already done above)
        # For subsequent days, just mark to market
        if i > warmup:
            portfolio.mark_to_market(close, date)
        elif i == warmup:
            portfolio.mark_to_market(close, date)

        portfolio.apply_daily_cash_interest()

    equity_curve = portfolio.get_equity_curve()
    final_equity = equity_curve.iloc[-1] if len(equity_curve) > 0 else initial_cash

    return BacktestResult(
        ticker=ticker,
        strategy_name="Buy & Hold",
        strategy_params={},
        equity_curve=equity_curve,
        trades=portfolio.trades,
        initial_cash=initial_cash,
        final_equity=final_equity,
    )
