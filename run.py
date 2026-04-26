"""Main entry point — run all strategies, produce report with tables, plots, and exports."""

import argparse
import os
import sys

from config import TICKERS, START_DATE, END_DATE, CAPITAL_PER_INDEX, RISK_FREE_RATE, OUTPUT_DIR
from data.fetcher import fetch_all
from engine.backtest import BacktestEngine, run_buy_and_hold
from metrics.performance import compute_metrics, compute_buy_and_hold_cagr, compute_aggregate_metrics
from reporting.tables import print_summary_table, print_top_strategies, print_best_per_index
from reporting.plots import generate_all_plots
from reporting.export import export_to_csv, export_to_excel
from strategies.registry import get_all_strategies


def parse_args():
    parser = argparse.ArgumentParser(description="ETF Momentum Backtest Engine")
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Ticker symbols to test (default: all from config)",
    )
    parser.add_argument(
        "--strategies", nargs="+", default=None,
        help="Strategy names to test (default: all)",
    )
    parser.add_argument(
        "--output-dir", default=OUTPUT_DIR,
        help="Output directory for plots and exports",
    )
    parser.add_argument(
        "--no-plots", action="store_true",
        help="Skip plot generation",
    )
    parser.add_argument(
        "--no-export", action="store_true",
        help="Skip CSV/Excel export",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 70)
    print("ETF MOMENTUM BACKTEST")
    print("=" * 70)

    # Select tickers
    tickers = TICKERS
    if args.tickers:
        tickers = {t: TICKERS.get(t, t) for t in args.tickers}

    # 1. Fetch data
    print("\n[1/6] Fetching data...")
    data = fetch_all(tickers, START_DATE, END_DATE)
    print(f"  Loaded {len(data)} indices")

    # 2. Get strategies
    all_strategies = get_all_strategies()
    if args.strategies:
        strategies = [s for s in all_strategies if s.name in args.strategies]
        missing = set(args.strategies) - {s.name for s in strategies}
        if missing:
            print(f"  WARNING: Unknown strategies: {missing}")
    else:
        strategies = all_strategies

    print(f"\n[2/6] Testing {len(strategies)} strategies × {len(data)} indices = {len(strategies) * len(data)} backtests")
    for s in strategies:
        print(f"  - {s.name} (warmup={s.warmup})")

    # 3. Run backtests
    print("\n[3/6] Running backtests...")
    all_metrics = []
    per_strategy_equity_curves = {}  # strategy_name -> {ticker: equity_curve}
    per_strategy_results = {}  # strategy_name -> {ticker: BacktestResult}
    buy_and_hold_cagrs = {}  # ticker -> CAGR
    buy_and_hold_results = {}  # ticker -> BacktestResult

    # Compute max warmup for fair buy-and-hold comparison
    max_warmup = max(s.warmup for s in strategies)

    # Compute buy-and-hold CAGRs and results
    for ticker, df in data.items():
        bah_cagr = compute_buy_and_hold_cagr(df, CAPITAL_PER_INDEX, warmup=max_warmup)
        buy_and_hold_cagrs[ticker] = bah_cagr
        bah_result = run_buy_and_hold(ticker, df, CAPITAL_PER_INDEX, RISK_FREE_RATE, warmup=max_warmup)
        buy_and_hold_results[ticker] = bah_result

    # Run each strategy for each ticker
    for si, strategy in enumerate(strategies):
        strategy_eq_curves = {}
        strategy_results = {}
        for ticker, df in data.items():
            engine = BacktestEngine(
                ticker=ticker,
                data=df,
                strategy=strategy,
                initial_cash=CAPITAL_PER_INDEX,
                risk_free_rate=RISK_FREE_RATE,
            )
            result = engine.run()
            metrics = compute_metrics(result, buy_and_hold_cagrs[ticker], RISK_FREE_RATE)
            all_metrics.append(metrics)
            strategy_eq_curves[ticker] = result.equity_curve
            strategy_results[ticker] = result

        per_strategy_equity_curves[strategy.name] = strategy_eq_curves
        per_strategy_results[strategy.name] = strategy_results

        if (si + 1) % 5 == 0 or si == len(strategies) - 1:
            print(f"  {si + 1}/{len(strategies)} strategies complete")

    # 4. Compute aggregate metrics
    print("\n[4/6] Computing aggregate portfolio metrics...")
    aggregate_metrics = []
    agg_bah_cagr = sum(buy_and_hold_cagrs.values()) / len(buy_and_hold_cagrs)

    # Track total trades per strategy for aggregate
    strategy_total_trades = {}
    for m in all_metrics:
        if m.strategy_name not in strategy_total_trades:
            strategy_total_trades[m.strategy_name] = 0
        strategy_total_trades[m.strategy_name] += m.num_trades

    for strategy_name, eq_curves in per_strategy_equity_curves.items():
        agg_metrics = compute_aggregate_metrics(
            eq_curves, strategy_name, agg_bah_cagr, RISK_FREE_RATE
        )
        agg_metrics.num_trades = strategy_total_trades.get(strategy_name, 0)
        aggregate_metrics.append(agg_metrics)

    # Add buy-and-hold aggregate
    bah_eq_curves = {ticker: buy_and_hold_results[ticker].equity_curve for ticker in data}
    bah_agg = compute_aggregate_metrics(bah_eq_curves, "Buy & Hold", agg_bah_cagr, RISK_FREE_RATE)
    aggregate_metrics.append(bah_agg)

    # 5. Print results
    print("\n[5/6] Results")

    # Aggregate portfolio results
    print_summary_table(aggregate_metrics, sort_by="sharpe_ratio", title="AGGREGATE PORTFOLIO RESULTS")

    # Top strategies by different metrics
    for metric in ["sharpe_ratio", "cagr", "alpha"]:
        print_top_strategies(aggregate_metrics, metric, n=5)

    # Per-ticker results
    print_summary_table(all_metrics, sort_by="sharpe_ratio", title="PER-TICKER RESULTS")

    # Best per index
    print_best_per_index(all_metrics, tickers)

    # Buy-and-hold comparison
    print(f"\n{'=' * 70}")
    print("BUY-AND-HOLD BASELINE")
    print(f"{'=' * 70}")
    for ticker in data:
        bah_metrics = [m for m in all_metrics if m.ticker == ticker and m.strategy_name == "Buy & Hold"]
        if not bah_metrics:
            # Compute from buy_and_hold_results
            bah_result = buy_and_hold_results[ticker]
            bah_m = compute_metrics(bah_result, buy_and_hold_cagrs[ticker], RISK_FREE_RATE)
        else:
            bah_m = bah_metrics[0]
        print(f"  {tickers[ticker]} ({ticker}): CAGR={buy_and_hold_cagrs[ticker]:.1%}")

    # 6. Generate plots and exports
    print(f"\n[6/6] Generating reports...")
    os.makedirs(args.output_dir, exist_ok=True)

    # Aggregate buy-and-hold equity curve
    all_dates = sorted(set().union(*[ec.index for ec in bah_eq_curves.values()]))
    combined = {}
    for d in all_dates:
        total = 0.0
        for ticker, ec in bah_eq_curves.items():
            if d in ec.index:
                total += ec.loc[d]
            else:
                # Forward-fill: find the last available value before d
                prior = ec[ec.index <= d]
                if len(prior) > 0:
                    total += prior.iloc[-1]
        combined[d] = total
    import pandas as pd
    bah_agg_ec = pd.Series(combined)

    if not args.no_plots:
        generate_all_plots(
            aggregate_metrics=aggregate_metrics,
            per_ticker_metrics=all_metrics,
            per_strategy_equity_curves=per_strategy_equity_curves,
            buy_and_hold_curves=bah_eq_curves,
            buy_and_hold_agg=bah_agg_ec,
            output_dir=args.output_dir,
        )

    if not args.no_export:
        # Export aggregate metrics
        export_to_csv(aggregate_metrics, os.path.join(args.output_dir, "aggregate_summary.csv"))
        # Export per-ticker metrics
        export_to_csv(all_metrics, os.path.join(args.output_dir, "per_ticker_summary.csv"))
        # Export equity curves
        all_ecs = {}
        for strat_name, ticker_ecs in per_strategy_equity_curves.items():
            for ticker, ec in ticker_ecs.items():
                all_ecs[f"{ticker}_{strat_name}"] = ec
        # Add buy-and-hold curves
        for ticker, ec in bah_eq_curves.items():
            all_ecs[f"{ticker}_BuyHold"] = ec
        export_to_excel(aggregate_metrics + all_metrics, all_ecs, os.path.join(args.output_dir, "full_results.xlsx"))
        print(f"  Exports saved to {args.output_dir}/")

    # Final summary
    print(f"\n{'=' * 70}")
    print("SUMMARY: STRATEGIES THAT BEAT BUY-AND-HOLD")
    print(f"{'=' * 70}")
    bah_cagr_val = bah_agg.cagr
    beaters = [m for m in aggregate_metrics if m.alpha > 0 and m.strategy_name != "Buy & Hold"]
    beaters.sort(key=lambda m: m.alpha, reverse=True)
    if beaters:
        for m in beaters:
            print(
                f"  {m.strategy_name}: CAGR={m.cagr:.1%} "
                f"(alpha={m.alpha:+.1%}), Sharpe={m.sharpe_ratio:.2f}, "
                f"MaxDD={m.max_drawdown:.1%}, #Trades={m.num_trades}"
            )
    else:
        print("  No strategy beat buy-and-hold on aggregate portfolio basis.")
        # Check per-ticker
        for ticker in data:
            ticker_metrics = [m for m in all_metrics if m.ticker == ticker and m.alpha > 0]
            if ticker_metrics:
                best = max(ticker_metrics, key=lambda m: m.alpha)
                print(f"  But {tickers[ticker]}: {best.strategy_name} (alpha={best.alpha:+.1%})")

    print(f"\nDone! Full results in {args.output_dir}/")


if __name__ == "__main__":
    main()
