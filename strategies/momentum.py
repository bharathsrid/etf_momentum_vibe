"""N-day return momentum strategy."""

import pandas as pd

from strategies.base import Signal, Strategy


class MomentumStrategy(Strategy):
    """Signal=INVESTED if N-day return is positive, else CASH."""

    def __init__(self, lookback: int):
        self.lookback = lookback

    @property
    def name(self) -> str:
        return f"MOM-{self.lookback}"

    @property
    def params(self) -> dict:
        return {"type": "momentum", "lookback": self.lookback}

    @property
    def warmup(self) -> int:
        return self.lookback

    def signal(self, data: pd.DataFrame) -> Signal:
        close = data["Close"]

        if len(close) <= self.lookback:
            return Signal.CASH

        current_close = close.iloc[-1]
        past_close = close.iloc[-self.lookback - 1]

        if past_close == 0:
            return Signal.CASH

        momentum = (current_close / past_close) - 1.0
        return Signal.INVESTED if momentum > 0 else Signal.CASH
