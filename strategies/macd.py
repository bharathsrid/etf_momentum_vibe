"""MACD-based strategy."""

import pandas as pd

from strategies.base import Signal, Strategy


class MACDStrategy(Strategy):
    """Signal=INVESTED if MACD line > Signal line, else CASH.

    MACD line = EMA(fast) - EMA(slow)
    Signal line = EMA(MACD line, signal_period)
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal_period: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal_period

    @property
    def name(self) -> str:
        return f"MACD_{self.fast}_{self.slow}_{self.signal_period}"

    @property
    def params(self) -> dict:
        return {
            "type": "macd",
            "fast": self.fast,
            "slow": self.slow,
            "signal_period": self.signal_period,
        }

    @property
    def warmup(self) -> int:
        return self.slow + self.signal_period

    def signal(self, data: pd.DataFrame) -> Signal:
        close = data["Close"]

        # Compute EMAs (adjust=False matches standard trading platform EMA)
        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]

        if pd.isna(current_macd) or pd.isna(current_signal):
            return Signal.CASH

        return Signal.INVESTED if current_macd > current_signal else Signal.CASH
