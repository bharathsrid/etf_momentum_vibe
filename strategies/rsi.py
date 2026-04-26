"""RSI-based strategies — basic threshold and hysteresis variants."""

import pandas as pd

from strategies.base import Signal, Strategy


def _compute_rsi(close: pd.Series, period: int) -> pd.Series:
    """Compute Relative Strength Index."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


class RSIThresholdStrategy(Strategy):
    """Signal=INVESTED if RSI > threshold (i.e., not oversold), else CASH.

    Simple threshold: invest if RSI is above the threshold.
    """

    def __init__(self, period: int = 14, threshold: float = 30.0):
        self.period = period
        self.threshold = threshold

    @property
    def name(self) -> str:
        return f"RSI_{self.period}_above_{int(self.threshold)}"

    @property
    def params(self) -> dict:
        return {
            "type": "rsi_threshold",
            "period": self.period,
            "threshold": self.threshold,
        }

    @property
    def warmup(self) -> int:
        return self.period + 1

    def signal(self, data: pd.DataFrame) -> Signal:
        close = data["Close"]
        rsi = _compute_rsi(close, self.period)
        current_rsi = rsi.iloc[-1]

        if pd.isna(current_rsi):
            return Signal.CASH

        return Signal.INVESTED if current_rsi > self.threshold else Signal.CASH


class RSIHysteresisStrategy(Strategy):
    """RSI with hysteresis bands — reduces whipsawing.

    When INVESTED: go to CASH only when RSI drops below upper_threshold.
    When in CASH: go to INVESTED only when RSI rises above lower_threshold.
    """

    def __init__(
        self,
        period: int = 14,
        lower_threshold: float = 30.0,
        upper_threshold: float = 70.0,
    ):
        self.period = period
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self._current_state: Signal = Signal.CASH

    @property
    def name(self) -> str:
        return f"RSI_{self.period}_{int(self.lower_threshold)}_{int(self.upper_threshold)}"

    @property
    def params(self) -> dict:
        return {
            "type": "rsi_hysteresis",
            "period": self.period,
            "lower_threshold": self.lower_threshold,
            "upper_threshold": self.upper_threshold,
        }

    @property
    def warmup(self) -> int:
        return self.period + 1

    def reset(self) -> None:
        """Reset internal state for a fresh backtest run."""
        self._current_state = Signal.CASH

    def signal(self, data: pd.DataFrame) -> Signal:
        close = data["Close"]
        rsi = _compute_rsi(close, self.period)
        current_rsi = rsi.iloc[-1]

        if pd.isna(current_rsi):
            return self._current_state

        if self._current_state == Signal.CASH:
            # Only switch to invested if RSI rises above lower threshold
            if current_rsi > self.lower_threshold:
                self._current_state = Signal.INVESTED
        else:
            # Only switch to cash if RSI drops below upper threshold
            if current_rsi < self.upper_threshold:
                self._current_state = Signal.CASH

        return self._current_state
