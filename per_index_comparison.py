"""Per-index comparison: best strategy vs buy-and-hold with full detail."""

from config import TICKERS, START_DATE, CAPITAL_PER_INDEX, RISK_FREE_RATE
from data.fetcher import fetch_all
from engine.backtest import BacktestEngine, run_buy_and_hold
from metrics.performance import compute_metrics
from strategies.registry import get_all_strategies


def main():
    # Fetch data
    print("Fetching data...")
    data = fetch_all(TICKERS, START_DATE)

    strategies = get_all_strategies()
    max_warmup = max(s.warmup for s in strategies)

    for ticker, name in TICKERS.items():
        if ticker not in data:
            continue

        df = data[ticker]

        # Buy-and-hold benchmark — derive baseline CAGR from B&H equity curve
        bah_result = run_buy_and_hold(ticker, df, CAPITAL_PER_INDEX, RISK_FREE_RATE, warmup=max_warmup)
        bah_metrics = compute_metrics(bah_result, None, RISK_FREE_RATE)
        bah_cagr = bah_metrics.cagr

        # Run all strategies
        best_sharpe = None
        best_cagr = None
        best_alpha = None
        all_results = []

        for strategy in strategies:
            engine = BacktestEngine(
                ticker=ticker,
                data=df,
                strategy=strategy,
                initial_cash=CAPITAL_PER_INDEX,
                risk_free_rate=RISK_FREE_RATE,
            )
            result = engine.run()
            metrics = compute_metrics(result, bah_cagr, RISK_FREE_RATE)
            all_results.append(metrics)

            if best_sharpe is None or metrics.sharpe_ratio > best_sharpe.sharpe_ratio:
                best_sharpe = metrics
            if best_cagr is None or metrics.cagr > best_cagr.cagr:
                best_cagr = metrics
            if best_alpha is None or metrics.alpha > best_alpha.alpha:
                best_alpha = metrics

        # Print detailed comparison
        print(f"\n{'=' * 80}")
        print(f"  {name} ({ticker})")
        print(f"  Period: {df.index[0].date()} to {df.index[-1].date()} ({len(df)} trading days)")
        print(f"  Starting Capital: ${CAPITAL_PER_INDEX:,.0f}")
        print(f"{'=' * 80}")

        # Buy & Hold
        print(f"\n  ┌─ BUY & HOLD ─────────────────────────────────────────────────────")
        print(f"  │  Final Value:    ${bah_metrics.total_return * CAPITAL_PER_INDEX + CAPITAL_PER_INDEX:>10,.2f}")
        print(f"  │  Total Return:   {bah_metrics.total_return:>9.1%}")
        print(f"  │  CAGR:           {bah_metrics.cagr:>9.1%}")
        print(f"  │  Max Drawdown:   {bah_metrics.max_drawdown:>9.1%}")
        print(f"  │  Sharpe Ratio:   {bah_metrics.sharpe_ratio:>9.2f}")
        print(f"  │  Sortino Ratio:  {bah_metrics.sortino_ratio:>9.2f}")
        print(f"  └─────────────────────────────────────────────────────────────────")

        # Best by Sharpe
        if best_sharpe:
            print(f"\n  ┌─ BEST BY SHARPE: {best_sharpe.strategy_name} ────────────────────────────")
            print(f"  │  Final Value:    ${best_sharpe.total_return * CAPITAL_PER_INDEX + CAPITAL_PER_INDEX:>10,.2f}")
            print(f"  │  Total Return:   {best_sharpe.total_return:>9.1%}  (vs B&H: {best_sharpe.total_return - bah_metrics.total_return:+.1%})")
            print(f"  │  CAGR:           {best_sharpe.cagr:>9.1%}  (vs B&H: {best_sharpe.cagr - bah_metrics.cagr:+.1%})")
            print(f"  │  Max Drawdown:   {best_sharpe.max_drawdown:>9.1%}  (vs B&H: {best_sharpe.max_drawdown - bah_metrics.max_drawdown:+.1%})")
            print(f"  │  Sharpe Ratio:   {best_sharpe.sharpe_ratio:>9.2f}  (vs B&H: {best_sharpe.sharpe_ratio - bah_metrics.sharpe_ratio:+.2f})")
            print(f"  │  Sortino Ratio:  {best_sharpe.sortino_ratio:>9.2f}  (vs B&H: {best_sharpe.sortino_ratio - bah_metrics.sortino_ratio:+.2f})")
            print(f"  │  Alpha:          {best_sharpe.alpha:>9.1%}")
            print(f"  │  # Trades:       {best_sharpe.num_trades:>9}")
            print(f"  │  Win Rate:       {best_sharpe.win_rate:>9.1%}")
            print(f"  └─────────────────────────────────────────────────────────────────")

        # Best by CAGR
        if best_cagr and best_cagr.strategy_name != best_sharpe.strategy_name:
            print(f"\n  ┌─ BEST BY CAGR: {best_cagr.strategy_name} ────────────────────────────────")
            print(f"  │  Final Value:    ${best_cagr.total_return * CAPITAL_PER_INDEX + CAPITAL_PER_INDEX:>10,.2f}")
            print(f"  │  CAGR:           {best_cagr.cagr:>9.1%}  (vs B&H: {best_cagr.cagr - bah_metrics.cagr:+.1%})")
            print(f"  │  Max Drawdown:   {best_cagr.max_drawdown:>9.1%}  (vs B&H: {best_cagr.max_drawdown - bah_metrics.max_drawdown:+.1%})")
            print(f"  │  Sharpe Ratio:   {best_cagr.sharpe_ratio:>9.2f}")
            print(f"  │  Alpha:          {best_cagr.alpha:>9.1%}")
            print(f"  │  # Trades:       {best_cagr.num_trades:>9}")
            print(f"  └─────────────────────────────────────────────────────────────────")

        # Best by Alpha
        if best_alpha and best_alpha.strategy_name != best_sharpe.strategy_name and best_alpha.strategy_name != best_cagr.strategy_name:
            print(f"\n  ┌─ BEST BY ALPHA: {best_alpha.strategy_name} ──────────────────────────────")
            print(f"  │  CAGR:           {best_alpha.cagr:>9.1%}  (vs B&H: {best_alpha.cagr - bah_metrics.cagr:+.1%})")
            print(f"  │  Alpha:          {best_alpha.alpha:>9.1%}")
            print(f"  │  Max Drawdown:   {best_alpha.max_drawdown:>9.1%}  (vs B&H: {best_alpha.max_drawdown - bah_metrics.max_drawdown:+.1%})")
            print(f"  │  Sharpe Ratio:   {best_alpha.sharpe_ratio:>9.2f}")
            print(f"  └─────────────────────────────────────────────────────────────────")

        # All strategies that beat buy-and-hold (positive alpha)
        beaters = sorted(
            [m for m in all_results if m.alpha > 0],
            key=lambda m: m.alpha,
            reverse=True,
        )
        if beaters:
            print(f"\n  ┌─ STRATEGIES THAT BEAT BUY-AND-HOLD ({len(beaters)}/{len(all_results)}) ──────────────────")
            print(f"  │ {'Strategy':<35} {'CAGR':>7} {'Alpha':>7} {'MaxDD':>7} {'Sharpe':>7} {'#Trd':>5} {'WinR':>5}")
            print(f"  │ {'─' * 35} {'─' * 7} {'─' * 7} {'─' * 7} {'─' * 7} {'─' * 5} {'─' * 5}")
            for m in beaters:
                print(f"  │ {m.strategy_name:<35} {m.cagr:>6.1%} {m.alpha:>6.1%} {m.max_drawdown:>6.1%} {m.sharpe_ratio:>7.2f} {m.num_trades:>5} {m.win_rate:>4.0%}")
            print(f"  └─────────────────────────────────────────────────────────────────")
        else:
            print(f"\n  ┌─ NO STRATEGY BEAT BUY-AND-HOLD ─────────────────────────────────")
            closest = sorted(all_results, key=lambda m: m.alpha, reverse=True)[:5]
            print(f"  │ Closest (by alpha):")
            for m in closest:
                print(f"  │   {m.strategy_name:<35} Alpha={m.alpha:+.1%}, CAGR={m.cagr:.1%}")
            print(f"  └─────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
