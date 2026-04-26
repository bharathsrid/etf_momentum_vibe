"""Dual SMA crossover strategy."""

import pandas as pd

from strategies.base import Signal, Strategy


class SMACrossoverStrategy(Strategy):
    """Signal=INVESTED if SMA(short) > SMA(long), else CASH."""

    def __init__(self, short_period: int, long_period: int):
        self.short_period = short_period
        self.long_period = long_period

    @property
    def name(self) -> str:
        return f"SMA_Cross_{self.short_period}_{self.long_period}"

    @property
    def params(self) -> dict:
        return {
            "type": "sma_crossover",
            "short_period": self.short_period,
            "long_period": self.long_period,
        }

    @property
    def warmup(self) -> int:
        return self.long_period

    def signal(self, data: pd.DataFrame) -> Signal:
        close = data["Close"]
        short_sma = close.rolling(window=self.short_period).mean()
        long_sma = close.rolling(window=self.long_period).mean()

        current_short = short_sma.iloc[-1]
        current_long = long_sma.iloc[-1]

        if pd.isna(current_long):
            return Signal.CASH

        return Signal.INVESTED if current_short > current_long else Signal.CASH
