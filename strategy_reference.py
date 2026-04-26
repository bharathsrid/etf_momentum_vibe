"""Export exact strategy definitions with their rules to a structured format."""

from strategies.registry import get_all_strategies


def describe_signal_logic(strategy) -> str:
    """Return a human-readable description of a strategy's signal logic."""
    name = strategy.name
    params = strategy.params
    stype = params.get("type", "")

    if stype == "sma_price":
        p = params["sma_period"]
        return f"INVESTED if Close > SMA(Close, {p}); else CASH"

    elif stype == "sma_crossover":
        s, l = params["short_period"], params["long_period"]
        return f"INVESTED if SMA(Close, {s}) > SMA(Close, {l}); else CASH"

    elif stype == "sma_slope":
        ma, sp = params["ma_period"], params["slope_period"]
        return f"INVESTED if (SMA[today] - SMA[today-{sp}]) / SMA[today-{sp}] > 0, where SMA = SMA(Close, {ma}); else CASH"

    elif stype == "momentum":
        lb = params["lookback"]
        return f"INVESTED if Close[today] / Close[today-{lb}] - 1 > 0; else CASH"

    elif stype == "macd":
        f, s, sig = params["fast"], params["slow"], params["signal_period"]
        return (f"INVESTED if MACD_line > Signal_line; else CASH\n"
                f"  MACD_line = EMA(Close, {f}) - EMA(Close, {s})\n"
                f"  Signal_line = EMA(MACD_line, {sig})")

    elif stype == "rsi_threshold":
        p, t = params["period"], params["threshold"]
        return (f"INVESTED if RSI({p}) > {t}; else CASH\n"
                f"  RSI uses EMA smoothing with alpha=1/{p}")

    elif stype == "rsi_hysteresis":
        p, lo, hi = params["period"], params["lower_threshold"], params["upper_threshold"]
        return (f"Stateful strategy with hysteresis bands:\n"
                f"  When CASH: switch to INVESTED if RSI({p}) > {lo}\n"
                f"  When INVESTED: switch to CASH if RSI({p}) < {hi}\n"
                f"  Reduces whipsawing between states")

    elif stype == "ts_momentum":
        lb, hp = params["lookback"], params["holding_period"]
        return (f"Stateful strategy with periodic rebalancing:\n"
                f"  Every {hp} trading days, compute {lb}-day return\n"
                f"  If return > 0: INVESTED for next {hp} days\n"
                f"  If return <= 0: CASH for next {hp} days\n"
                f"  Signal held constant between rebalancing dates")

    elif stype == "combo":
        mode = params["mode"]
        subs = params["sub_strategies"]
        sub_descriptions = []
        for sub in subs:
            sub_type = sub.get("type", "")
            if sub_type == "sma_price":
                sub_descriptions.append(f"Close > SMA({sub['sma_period']})")
            elif sub_type == "sma_crossover":
                sub_descriptions.append(f"SMA({sub['short_period']}) > SMA({sub['long_period']})")
            elif sub_type == "sma_slope":
                sub_descriptions.append(f"SMA({sub['ma_period']}) slope({sub['slope_period']}d) > 0")
            elif sub_type == "momentum":
                sub_descriptions.append(f"{sub['lookback']}-day return > 0")
            elif sub_type == "macd":
                sub_descriptions.append(f"MACD({sub['fast']},{sub['slow']},{sub['signal_period']}) bullish")
            elif sub_type == "rsi_threshold":
                sub_descriptions.append(f"RSI({sub['period']}) > {sub['threshold']}")
            elif sub_type == "rsi_hysteresis":
                sub_descriptions.append(f"RSI({sub['period']}) hysteresis {sub['lower_threshold']}/{sub['upper_threshold']}")
            else:
                sub_descriptions.append(str(sub))

        if mode == "AND":
            rule = " AND ".join(sub_descriptions)
            return f"INVESTED if ALL of the following are true:\n  {rule}\n  else CASH"
        elif mode == "OR":
            rule = " OR ".join(sub_descriptions)
            return f"INVESTED if ANY of the following are true:\n  {rule}\n  else CASH"
        elif mode == "MAJORITY":
            n = len(sub_descriptions)
            needed = n // 2 + 1
            rule = "\n  ".join(f"({i+1}) {d}" for i, d in enumerate(sub_descriptions))
            return f"INVESTED if {needed}+ of {n} signals are bullish:\n  {rule}\n  else CASH"

    return f"Strategy: {name}"


def main():
    strategies = get_all_strategies()

    print("=" * 80)
    print("COMPLETE STRATEGY REFERENCE")
    print(f"Total strategies: {len(strategies)}")
    print("=" * 80)

    # Group by type
    groups = {}
    for s in strategies:
        stype = s.params.get("type", "unknown")
        if stype not in groups:
            groups[stype] = []
        groups[stype].append(s)

    for stype, strats in groups.items():
        print(f"\n{'─' * 80}")
        print(f"  {stype.upper()} STRATEGIES ({len(strats)} strategies)")
        print(f"{'─' * 80}")

        for s in strats:
            print(f"\n  ┌─ {s.name} ─────────────────────────────")
            print(f"  │  Warmup: {s.warmup} bars")
            print(f"  │  Parameters: {s.params}")
            desc = describe_signal_logic(s)
            for line in desc.split("\n"):
                print(f"  │  Rule: {line}")
            print(f"  └──────────────────────────────────────")


if __name__ == "__main__":
    main()
