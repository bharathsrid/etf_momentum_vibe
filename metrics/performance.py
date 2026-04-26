"""Performance metrics calculation for backtest results."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine.backtest import BacktestResult


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single backtest result."""
    ticker: str
    strategy_name: str
    strategy_params: dict

    # Core returns
    total_return: float          # (final / initial) - 1
    cagr: float                  # Compound annual growth rate

    # Risk
    max_drawdown: float          # Worst peak-to-trough decline (negative number)
    annual_volatility: float     # Annualized standard deviation of returns

    # Risk-adjusted
    sharpe_ratio: float          # Annualized Sharpe (rf=2%)
    sortino_ratio: float         # Annualized Sortino (rf=2%, downside dev)

    # Trading stats
    num_trades: int
    win_rate: float              # % of profitable round-trip trades

    # vs benchmark
    alpha: float                 # CAGR - buy_and_hold_cagr (set after computation)


def compute_metrics(
    result: BacktestResult,
    buy_and_hold_cagr: float | None = None,
    risk_free_rate: float = 0.02,
) -> PerformanceMetrics:
    """Compute all performance metrics for a single backtest result."""
    ec = result.equity_curve

    if len(ec) < 2:
        return PerformanceMetrics(
            ticker=result.ticker,
            strategy_name=result.strategy_name,
            strategy_params=result.strategy_params,
            total_return=0.0,
            cagr=0.0,
            max_drawdown=0.0,
            annual_volatility=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            num_trades=0,
            win_rate=0.0,
            alpha=0.0,
        )

    # Total return
    total_return = (ec.iloc[-1] / ec.iloc[0]) - 1.0

    # CAGR
    num_days = len(ec)
    years = num_days / 252
    if years > 0 and ec.iloc[-1] > 0 and ec.iloc[0] > 0:
        cagr = (ec.iloc[-1] / ec.iloc[0]) ** (1.0 / years) - 1.0
    else:
        cagr = 0.0

    # Daily returns
    daily_returns = ec.pct_change().dropna()

    # Max drawdown
    running_peak = ec.cummax()
    drawdown = ec / running_peak - 1.0
    max_drawdown = drawdown.min()

    # Annualized volatility
    if len(daily_returns) > 1:
        annual_volatility = daily_returns.std() * np.sqrt(252)
    else:
        annual_volatility = 0.0

    # Sharpe ratio
    rf_daily = risk_free_rate / 252
    excess_returns = daily_returns - rf_daily
    if len(excess_returns) > 1 and excess_returns.std() > 0:
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0

    # Sortino ratio: RMS of min(excess, 0) over the FULL sample
    if len(excess_returns) > 1:
        downside = excess_returns.clip(upper=0.0)
        downside_dev = np.sqrt((downside ** 2).mean()) * np.sqrt(252)
        sortino_ratio = (excess_returns.mean() * 252) / downside_dev if downside_dev > 0 else 0.0
    else:
        sortino_ratio = 0.0

    # Number of trades
    num_trades = len(result.trades)

    # Win rate: pair up BUY/SELL trades as round trips
    win_rate = _compute_win_rate(result.trades, result.equity_curve)

    # Alpha vs buy-and-hold
    alpha = cagr - buy_and_hold_cagr if buy_and_hold_cagr is not None else 0.0

    return PerformanceMetrics(
        ticker=result.ticker,
        strategy_name=result.strategy_name,
        strategy_params=result.strategy_params,
        total_return=total_return,
        cagr=cagr,
        max_drawdown=max_drawdown,
        annual_volatility=annual_volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        num_trades=num_trades,
        win_rate=win_rate,
        alpha=alpha,
    )


def _compute_win_rate(trades: list, equity_curve: pd.Series) -> float:
    """Compute win rate from a list of BUY/SELL trade pairs.

    Pairs consecutive BUY and SELL trades. If the last trade is a BUY
    (unclosed position), close it at the last equity curve value.
    """
    if not trades:
        return 0.0

    round_trips = 0
    wins = 0
    buy_price = None

    for trade in trades:
        if trade.action == "BUY":
            buy_price = trade.price
        elif trade.action == "SELL" and buy_price is not None:
            round_trips += 1
            if trade.price > buy_price:
                wins += 1
            buy_price = None

    # Handle unclosed position at end
    if buy_price is not None and len(equity_curve) > 0:
        # Approximate: if final equity > initial, it's a win
        round_trips += 1
        last_close_approx = equity_curve.iloc[-1]
        if last_close_approx > buy_price:
            wins += 1

    return wins / round_trips if round_trips > 0 else 0.0


def compute_buy_and_hold_cagr(
    data: pd.DataFrame,
    initial_cash: float,
    warmup: int = 0,
) -> float:
    """Compute CAGR for buy-and-hold from first available open after warmup to end."""
    if warmup >= len(data):
        return 0.0

    buy_price = data["Open"].iloc[warmup]
    shares = initial_cash / buy_price
    final_value = shares * data["Close"].iloc[-1]

    num_days = len(data) - warmup
    years = num_days / 252

    if years > 0 and final_value > 0 and initial_cash > 0:
        return (final_value / initial_cash) ** (1.0 / years) - 1.0
    return 0.0


def compute_aggregate_metrics(
    per_ticker_equity_curves: dict[str, pd.Series],
    strategy_name: str,
    buy_and_hold_cagr: float | None = None,
    risk_free_rate: float = 0.02,
) -> PerformanceMetrics:
    """Compute aggregate portfolio metrics from per-ticker equity curves.

    The aggregate equity curve is the sum of all per-ticker equity curves.
    Different indices may have different trading calendars, so we forward-fill
    missing dates before summing.
    """
    # Get the union of all dates
    all_dates = sorted(set().union(*[ec.index for ec in per_ticker_equity_curves.values()]))
    combined = pd.DataFrame(index=all_dates)

    for ticker, ec in per_ticker_equity_curves.items():
        combined[ticker] = ec
        combined[ticker] = combined[ticker].ffill()  # forward-fill missing dates

    # Drop any initial NaN rows (before all indices have data)
    combined = combined.dropna()

    aggregate_ec = combined.sum(axis=1)

    # Create a pseudo-result for metric computation
    class PseudoResult:
        def __init__(self, ec):
            self.ticker = "AGGREGATE"
            self.strategy_name = strategy_name
            self.strategy_params = {}
            self.equity_curve = ec
            self.trades = []

    result = PseudoResult(aggregate_ec)
    return compute_metrics(result, buy_and_hold_cagr, risk_free_rate)
