"""Combination strategies — combine multiple sub-strategies with AND/OR/MAJORITY logic."""

from strategies.base import Signal, Strategy


class ComboStrategy(Strategy):
    """Combine multiple sub-strategies.

    mode="AND": INVESTED only if ALL sub-strategies say INVESTED.
    mode="OR": INVESTED if ANY sub-strategy says INVESTED.
    mode="MAJORITY": INVESTED if majority of sub-strategies say INVESTED.
    """

    def __init__(self, strategies: list[Strategy], mode: str = "AND", label: str = ""):
        self.strategies = strategies
        self.mode = mode.upper()
        self.label = label

    @property
    def name(self) -> str:
        if self.label:
            return self.label
        # Auto-generate name from sub-strategies
        sub_names = "_".join(s.name for s in self.strategies)
        return f"Combo_{self.mode}_{sub_names}"

    @property
    def params(self) -> dict:
        return {
            "type": "combo",
            "mode": self.mode,
            "sub_strategies": [s.params for s in self.strategies],
        }

    @property
    def warmup(self) -> int:
        return max(s.warmup for s in self.strategies)

    def reset(self) -> None:
        """Reset all sub-strategies."""
        for s in self.strategies:
            s.reset()

    def signal(self, data) -> Signal:
        signals = [s.signal(data) for s in self.strategies]

        if self.mode == "AND":
            return Signal.INVESTED if all(sig == Signal.INVESTED for sig in signals) else Signal.CASH

        elif self.mode == "OR":
            return Signal.INVESTED if any(sig == Signal.INVESTED for sig in signals) else Signal.CASH

        elif self.mode == "MAJORITY":
            invested_count = sum(1 for sig in signals if sig == Signal.INVESTED)
            return Signal.INVESTED if invested_count > len(signals) / 2 else Signal.CASH

        else:
            raise ValueError(f"Unknown combo mode: {self.mode}")
