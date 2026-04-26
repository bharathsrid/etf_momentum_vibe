"""CSV and Excel export for backtest results."""

import os

import pandas as pd

from metrics.performance import PerformanceMetrics


def export_to_csv(
    metrics_list: list[PerformanceMetrics],
    filepath: str,
) -> None:
    """Export metrics to CSV."""
    rows = []
    for m in metrics_list:
        rows.append({
            "Ticker": m.ticker,
            "Strategy": m.strategy_name,
            "Total Return": m.total_return,
            "CAGR": m.cagr,
            "Max Drawdown": m.max_drawdown,
            "Annual Volatility": m.annual_volatility,
            "Sharpe Ratio": m.sharpe_ratio,
            "Sortino Ratio": m.sortino_ratio,
            "Num Trades": m.num_trades,
            "Win Rate": m.win_rate,
            "Alpha": m.alpha,
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)


def export_to_excel(
    metrics_list: list[PerformanceMetrics],
    equity_curves: dict[str, pd.Series],
    filepath: str,
) -> None:
    """Export metrics + equity curves to multi-sheet Excel."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        # Metrics sheet
        rows = []
        for m in metrics_list:
            rows.append({
                "Ticker": m.ticker,
                "Strategy": m.strategy_name,
                "Total Return": m.total_return,
                "CAGR": m.cagr,
                "Max Drawdown": m.max_drawdown,
                "Annual Volatility": m.annual_volatility,
                "Sharpe Ratio": m.sharpe_ratio,
                "Sortino Ratio": m.sortino_ratio,
                "Num Trades": m.num_trades,
                "Win Rate": m.win_rate,
                "Alpha": m.alpha,
            })
        metrics_df = pd.DataFrame(rows)
        metrics_df.to_excel(writer, sheet_name="Metrics", index=False)

        # Equity curves sheet (each strategy as a column)
        ec_df = pd.DataFrame(equity_curves)
        ec_df.to_excel(writer, sheet_name="Equity Curves")
