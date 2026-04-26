"""Console table output for backtest results."""

from tabulate import tabulate

from metrics.performance import PerformanceMetrics


def print_summary_table(
    metrics_list: list[PerformanceMetrics],
    sort_by: str = "sharpe_ratio",
    title: str = "RESULTS",
) -> None:
    """Print a summary table of strategies, sorted by the given metric."""
    sorted_metrics = sorted(metrics_list, key=lambda m: getattr(m, sort_by), reverse=True)

    headers = ["Strategy", "Total Ret", "CAGR", "MaxDD", "Sharpe", "Sortino", "#Trades", "Alpha"]
    rows = []
    for m in sorted_metrics:
        rows.append([
            m.strategy_name,
            f"{m.total_return:.1%}",
            f"{m.cagr:.1%}",
            f"{m.max_drawdown:.1%}",
            f"{m.sharpe_ratio:.2f}",
            f"{m.sortino_ratio:.2f}",
            m.num_trades,
            f"{m.alpha:.1%}",
        ])

    print(f"\n{'=' * 90}")
    print(f"{title} (sorted by {sort_by})")
    print(f"{'=' * 90}")
    print(tabulate(rows, headers=headers, tablefmt="rounded_grid"))


def print_per_ticker_table(
    metrics_by_ticker: dict[str, list[PerformanceMetrics]],
    ticker_names: dict[str, str],
    sort_by: str = "sharpe_ratio",
) -> None:
    """Print per-ticker breakdown of results."""
    for ticker, metrics in metrics_by_ticker.items():
        name = ticker_names.get(ticker, ticker)
        print_summary_table(metrics, sort_by=sort_by, title=f"{name} ({ticker})")


def print_top_strategies(
    metrics_list: list[PerformanceMetrics],
    metric: str,
    n: int = 5,
) -> None:
    """Print top N strategies by a given metric."""
    sorted_metrics = sorted(metrics_list, key=lambda m: getattr(m, metric), reverse=True)
    label = metric.replace("_", " ").title()

    print(f"\n{'=' * 70}")
    print(f"TOP {n} BY {label.upper()}")
    print(f"{'=' * 70}")
    for i, m in enumerate(sorted_metrics[:n], 1):
        print(
            f"  {i}. {m.strategy_name}: "
            f"{label}={getattr(m, metric):.2f}, "
            f"CAGR={m.cagr:.1%}, "
            f"MaxDD={m.max_drawdown:.1%}, "
            f"Alpha={m.alpha:.1%}"
        )


def print_best_per_index(
    all_metrics: list[PerformanceMetrics],
    ticker_names: dict[str, str],
) -> None:
    """Print the best strategy for each index."""
    print(f"\n{'=' * 70}")
    print("BEST STRATEGY PER INDEX (by Sharpe)")
    print(f"{'=' * 70}")

    tickers = set(m.ticker for m in all_metrics)
    for ticker in sorted(tickers):
        ticker_metrics = [m for m in all_metrics if m.ticker == ticker]
        if not ticker_metrics:
            continue
        best = max(ticker_metrics, key=lambda m: m.sharpe_ratio)
        name = ticker_names.get(ticker, ticker)
        print(f"  {name} ({ticker}): {best.strategy_name}")
        print(
            f"    CAGR={best.cagr:.1%}, Sharpe={best.sharpe_ratio:.2f}, "
            f"MaxDD={best.max_drawdown:.1%}, Alpha={best.alpha:.1%}"
        )
