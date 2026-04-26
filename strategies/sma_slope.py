"""MA slope-based strategy — invest when the slope of a moving average is positive."""

import pandas as pd

from strategies.base import Signal, Strategy


class SMASlopeStrategy(Strategy):
    """Signal=INVESTED if the N-day slope of M-day SMA is positive, else CASH.

    Slope is calculated as: (SMA[today] - SMA[today - slope_period]) / SMA[today - slope_period]
    """

    def __init__(self, ma_period: int, slope_period: int):
        self.ma_period = ma_period
        self.slope_period = slope_period

    @property
    def name(self) -> str:
        return f"SMA_Slope_{self.ma_period}_{self.slope_period}"

    @property
    def params(self) -> dict:
        return {
            "type": "sma_slope",
            "ma_period": self.ma_period,
            "slope_period": self.slope_period,
        }

    @property
    def warmup(self) -> int:
        return self.ma_period + self.slope_period

    def signal(self, data: pd.DataFrame) -> Signal:
        close = data["Close"]
        sma = close.rolling(window=self.ma_period).mean()

        if len(sma) < self.slope_period + 1:
            return Signal.CASH

        current_sma = sma.iloc[-1]
        past_sma = sma.iloc[-self.slope_period - 1]

        if pd.isna(current_sma) or pd.isna(past_sma) or past_sma == 0:
            return Signal.CASH

        slope = (current_sma - past_sma) / past_sma
        return Signal.INVESTED if slope > 0 else Signal.CASH
