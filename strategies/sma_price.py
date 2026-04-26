"""Price above/below N-day Simple Moving Average strategy."""

import pandas as pd

from strategies.base import Signal, Strategy


class SMAPriceStrategy(Strategy):
    """Signal=INVESTED if Close > SMA(Close, period), else CASH."""

    def __init__(self, sma_period: int):
        self.sma_period = sma_period

    @property
    def name(self) -> str:
        return f"SMA-{self.sma_period}"

    @property
    def params(self) -> dict:
        return {"type": "sma_price", "sma_period": self.sma_period}

    @property
    def warmup(self) -> int:
        return self.sma_period

    def signal(self, data: pd.DataFrame) -> Signal:
        close = data["Close"]
        sma = close.rolling(window=self.sma_period).mean()
        current_close = close.iloc[-1]
        current_sma = sma.iloc[-1]

        if pd.isna(current_sma):
            return Signal.CASH

        return Signal.INVESTED if current_close > current_sma else Signal.CASH
