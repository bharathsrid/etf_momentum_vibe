"""Time-series momentum strategy — evaluate momentum at fixed rebalancing intervals."""

import pandas as pd

from strategies.base import Signal, Strategy


class TSMomentumStrategy(Strategy):
    """Time-series momentum: evaluate lookback-period return at fixed intervals.

    At each rebalancing point (every holding_period days), compute the
    lookback-day return. If positive → INVESTED for next holding_period;
    if negative → CASH for next holding_period.
    Between rebalancing points, the signal is held constant.
    """

    def __init__(self, lookback: int, holding_period: int):
        self.lookback = lookback
        self.holding_period = holding_period
        self._bars_since_rebalance: int = 0
        self._current_signal: Signal = Signal.CASH

    @property
    def name(self) -> str:
        return f"TSMOM_{self.lookback}_{self.holding_period}"

    @property
    def params(self) -> dict:
        return {
            "type": "ts_momentum",
            "lookback": self.lookback,
            "holding_period": self.holding_period,
        }

    @property
    def warmup(self) -> int:
        return self.lookback

    def reset(self) -> None:
        """Reset internal state for a fresh backtest run."""
        self._bars_since_rebalance = 0
        self._current_signal = Signal.CASH

    def signal(self, data: pd.DataFrame) -> Signal:
        # Check if it's time to rebalance
        if self._bars_since_rebalance == 0:
            close = data["Close"]

            if len(close) > self.lookback:
                current_close = close.iloc[-1]
                past_close = close.iloc[-self.lookback - 1]

                if past_close > 0:
                    momentum = (current_close / past_close) - 1.0
                    self._current_signal = Signal.INVESTED if momentum > 0 else Signal.CASH
                else:
                    self._current_signal = Signal.CASH

            self._bars_since_rebalance = self.holding_period

        self._bars_since_rebalance -= 1
        return self._current_signal
