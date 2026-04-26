"""Abstract base class and Signal enum for all trading strategies."""

from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd


class Signal(Enum):
    """Trading signal: either invested in the index or in cash."""
    INVESTED = 1
    CASH = 0


class Strategy(ABC):
    """Abstract base class for all trading strategies.

    Each strategy must implement:
    - name: unique string identifier
    - params: dict of parameters for reproducibility
    - warmup: minimum bars needed before first signal
    - signal(): given data up to current bar, return INVESTED or CASH
    - reset(): reset any internal state (for stateful strategies)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy name (e.g., 'SMA-200', 'MACD_12_26_9')."""
        ...

    @property
    @abstractmethod
    def params(self) -> dict:
        """Strategy parameters for logging/reproducibility."""
        ...

    @property
    @abstractmethod
    def warmup(self) -> int:
        """Minimum number of bars needed before the first signal can be generated."""
        ...

    @abstractmethod
    def signal(self, data: pd.DataFrame) -> Signal:
        """Given data up to and including current bar, return INVESTED or CASH.

        Args:
            data: DataFrame with columns Open, High, Low, Close, Volume.
                  The last row (iloc[-1]) is 'today'.

        Returns:
            Signal.INVESTED or Signal.CASH
        """
        ...

    def reset(self) -> None:
        """Reset any internal state. Called before each backtest run.

        Default implementation is a no-op (for stateless strategies).
        Stateful strategies (RSI hysteresis, TSMOM) should override this.
        """
        pass
