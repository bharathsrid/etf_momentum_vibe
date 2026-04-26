"""Equity curve charts, drawdown plots, and strategy comparison visualizations."""

import os
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from metrics.performance import PerformanceMetrics


def plot_equity_curves(
    results: dict[str, pd.Series],  # strategy_name -> equity_curve
    buy_and_hold: pd.Series,
    title: str,
    output_path: str,
    top_n: int = 5,
    sort_by: str = "sharpe_ratio",
    metrics: Optional[list[PerformanceMetrics]] = None,
) -> None:
    """Plot equity curves of top N strategies vs buy-and-hold."""
    fig, ax = plt.subplots(figsize=(14, 7))

    # If metrics provided, sort and pick top N
    if metrics:
        sorted_metrics = sorted(metrics, key=lambda m: getattr(m, sort_by), reverse=True)
        top_names = [m.strategy_name for m in sorted_metrics[:top_n]]
    else:
        top_names = list(results.keys())[:top_n]

    # Plot buy and hold
    ax.plot(buy_and_hold.index, buy_and_hold.values, "k--", linewidth=2, label="Buy & Hold", alpha=0.7)

    # Plot top strategies
    colors = plt.cm.Set2.colors
    for i, name in enumerate(top_names):
        if name in results:
            ec = results[name]
            ax.plot(ec.index, ec.values, linewidth=1.5, label=name, color=colors[i % len(colors)])

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel("Portfolio Value ($)")
    ax.set_xlabel("Date")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_drawdown(
    equity_curve: pd.Series,
    strategy_name: str,
    output_path: str,
) -> None:
    """Plot drawdown chart for a single strategy."""
    running_peak = equity_curve.cummax()
    drawdown = equity_curve / running_peak - 1.0

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(drawdown.index, drawdown.values, 0, color="red", alpha=0.3)
    ax.plot(drawdown.index, drawdown.values, color="red", linewidth=0.8)

    ax.set_title(f"Drawdown: {strategy_name}", fontsize=14, fontweight="bold")
    ax.set_ylabel("Drawdown")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_strategy_comparison(
    metrics_list: list[PerformanceMetrics],
    output_path: str,
    top_n: int = 15,
) -> None:
    """Bar chart comparing key metrics across strategies."""
    # Sort by Sharpe and take top N
    sorted_metrics = sorted(metrics_list, key=lambda m: m.sharpe_ratio, reverse=True)[:top_n]
    names = [m.strategy_name for m in sorted_metrics]
    cagrs = [m.cagr * 100 for m in sorted_metrics]
    max_dds = [m.max_drawdown * 100 for m in sorted_metrics]
    sharpes = [m.sharpe_ratio for m in sorted_metrics]

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    # CAGR
    bars = axes[0].barh(range(len(names)), cagrs, color="steelblue", alpha=0.8)
    axes[0].set_yticks(range(len(names)))
    axes[0].set_yticklabels(names, fontsize=8)
    axes[0].set_xlabel("CAGR (%)")
    axes[0].set_title("CAGR", fontweight="bold")
    axes[0].invert_yaxis()

    # Max Drawdown
    axes[1].barh(range(len(names)), max_dds, color="coral", alpha=0.8)
    axes[1].set_yticks(range(len(names)))
    axes[1].set_yticklabels(names, fontsize=8)
    axes[1].set_xlabel("Max Drawdown (%)")
    axes[1].set_title("Max Drawdown", fontweight="bold")
    axes[1].invert_yaxis()

    # Sharpe Ratio
    axes[2].barh(range(len(names)), sharpes, color="seagreen", alpha=0.8)
    axes[2].set_yticks(range(len(names)))
    axes[2].set_yticklabels(names, fontsize=8)
    axes[2].set_xlabel("Sharpe Ratio")
    axes[2].set_title("Sharpe Ratio", fontweight="bold")
    axes[2].invert_yaxis()

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_all_plots(
    aggregate_metrics: list[PerformanceMetrics],
    per_ticker_metrics: list[PerformanceMetrics],
    per_strategy_equity_curves: dict[str, dict[str, pd.Series]],
    buy_and_hold_curves: dict[str, pd.Series],
    buy_and_hold_agg: pd.Series,
    output_dir: str,
) -> None:
    """Generate all plots for the backtest results."""
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    # Aggregate equity curves
    agg_ecs = {}
    for strat_name, ticker_ecs in per_strategy_equity_curves.items():
        all_dates = sorted(set().union(*[ec.index for ec in ticker_ecs.values()]))
        combined = pd.DataFrame(index=all_dates)
        for ticker, ec in ticker_ecs.items():
            combined[ticker] = ec
            combined[ticker] = combined[ticker].ffill()
        combined = combined.dropna()
        agg_ecs[strat_name] = combined.sum(axis=1)

    plot_equity_curves(
        agg_ecs,
        buy_and_hold_agg,
        "Aggregate Portfolio: Top Strategies vs Buy & Hold",
        os.path.join(plots_dir, "equity_aggregate.png"),
        top_n=5,
        metrics=aggregate_metrics,
    )

    # Per-ticker equity curves
    ticker_names = {
        "^GSPC": "S&P 500",
        "^FTSE": "FTSE 100",
        "^NSEI": "Nifty 50",
        "^STOXX50E": "STOXX 50",
    }
    for ticker, bah_ec in buy_and_hold_curves.items():
        ticker_ecs = {}
        for strat_name, ticker_ec_dict in per_strategy_equity_curves.items():
            if ticker in ticker_ec_dict:
                ticker_ecs[strat_name] = ticker_ec_dict[ticker]

        ticker_metrics = [m for m in per_ticker_metrics if m.ticker == ticker]
        name = ticker_names.get(ticker, ticker)

        plot_equity_curves(
            ticker_ecs,
            bah_ec,
            f"{name}: Top Strategies vs Buy & Hold",
            os.path.join(plots_dir, f"equity_{ticker.replace('^', '')}.png"),
            top_n=5,
            metrics=ticker_metrics,
        )

    # Strategy comparison bar chart
    plot_strategy_comparison(
        aggregate_metrics,
        os.path.join(plots_dir, "strategy_comparison.png"),
    )

    # Drawdown for top 5 aggregate strategies
    sorted_agg = sorted(aggregate_metrics, key=lambda m: m.sharpe_ratio, reverse=True)
    for i, m in enumerate(sorted_agg[:5]):
        if m.strategy_name in agg_ecs:
            plot_drawdown(
                agg_ecs[m.strategy_name],
                m.strategy_name,
                os.path.join(plots_dir, f"drawdown_{i+1}_{m.strategy_name}.png"),
            )

    print(f"  Plots saved to {plots_dir}/")
