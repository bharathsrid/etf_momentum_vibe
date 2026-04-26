"""Central registry of all strategy instances to be tested."""

from strategies.base import Strategy
from strategies.sma_price import SMAPriceStrategy
from strategies.sma_crossover import SMACrossoverStrategy
from strategies.sma_slope import SMASlopeStrategy
from strategies.momentum import MomentumStrategy
from strategies.macd import MACDStrategy
from strategies.rsi import RSIThresholdStrategy, RSIHysteresisStrategy
from strategies.time_series_momentum import TSMomentumStrategy
from strategies.combo import ComboStrategy


def get_all_strategies() -> list[Strategy]:
    """Return every strategy instance to be tested (39 total)."""
    strategies = []

    # ── SMA Price (5 strategies) ──
    for period in [10, 20, 50, 100, 200]:
        strategies.append(SMAPriceStrategy(period))

    # ── SMA Crossover (6 strategies) ──
    for short, long in [(10, 20), (10, 50), (20, 50), (20, 100), (50, 100), (50, 200)]:
        strategies.append(SMACrossoverStrategy(short, long))

    # ── SMA Slope (4 strategies) ──
    strategies.append(SMASlopeStrategy(ma_period=50, slope_period=10))
    strategies.append(SMASlopeStrategy(ma_period=50, slope_period=20))
    strategies.append(SMASlopeStrategy(ma_period=200, slope_period=20))
    strategies.append(SMASlopeStrategy(ma_period=200, slope_period=50))

    # ── Momentum (5 strategies) ──
    for lookback in [5, 21, 63, 126, 252]:
        strategies.append(MomentumStrategy(lookback))

    # ── MACD (3 strategies) ──
    strategies.append(MACDStrategy(fast=12, slow=26, signal_period=9))    # classic
    strategies.append(MACDStrategy(fast=8, slow=17, signal_period=9))     # faster
    strategies.append(MACDStrategy(fast=19, slow=39, signal_period=9))    # slower

    # ── RSI (4 strategies) ──
    strategies.append(RSIThresholdStrategy(period=14, threshold=30))      # basic: invest if not oversold
    strategies.append(RSIHysteresisStrategy(period=14, lower_threshold=30, upper_threshold=70))  # hysteresis 30/70
    strategies.append(RSIHysteresisStrategy(period=14, lower_threshold=40, upper_threshold=60))  # hysteresis 40/60
    strategies.append(RSIHysteresisStrategy(period=21, lower_threshold=35, upper_threshold=65))  # hysteresis 35/65

    # ── Time-Series Momentum (4 strategies) ──
    strategies.append(TSMomentumStrategy(lookback=252, holding_period=21))   # 12mo look, 1mo hold
    strategies.append(TSMomentumStrategy(lookback=252, holding_period=63))   # 12mo look, 3mo hold
    strategies.append(TSMomentumStrategy(lookback=126, holding_period=21))   # 6mo look, 1mo hold
    strategies.append(TSMomentumStrategy(lookback=63, holding_period=21))    # 3mo look, 1mo hold

    # ── Combo strategies (8 strategies) ──
    # 1. Close > 200 SMA AND 50 SMA slope positive (10-day)
    strategies.append(ComboStrategy(
        strategies=[
            SMAPriceStrategy(200),
            SMASlopeStrategy(50, 10),
        ],
        mode="AND",
        label="Combo_200SMA_AND_50SMA_Slope10",
    ))

    # 2. Close > 50 SMA AND Close > 200 SMA (double trend filter)
    strategies.append(ComboStrategy(
        strategies=[
            SMAPriceStrategy(50),
            SMAPriceStrategy(200),
        ],
        mode="AND",
        label="Combo_50SMA_AND_200SMA",
    ))

    # 3. 12-month momentum > 0 AND Close > 200 SMA (momentum + trend)
    strategies.append(ComboStrategy(
        strategies=[
            MomentumStrategy(252),
            SMAPriceStrategy(200),
        ],
        mode="AND",
        label="Combo_MOM252_AND_200SMA",
    ))

    # 4. MACD bullish AND RSI(14) > 40 (momentum + not weak)
    strategies.append(ComboStrategy(
        strategies=[
            MACDStrategy(12, 26, 9),
            RSIThresholdStrategy(14, 40),
        ],
        mode="AND",
        label="Combo_MACD_AND_RSI14_A40",
    ))

    # 5. Close > 50 SMA OR 6-month momentum > 0 (relaxed entry)
    strategies.append(ComboStrategy(
        strategies=[
            SMAPriceStrategy(50),
            MomentumStrategy(126),
        ],
        mode="OR",
        label="Combo_50SMA_OR_MOM126",
    ))

    # 6. MAJORITY of: Close > 50 SMA, Close > 200 SMA, 3-month momentum > 0
    strategies.append(ComboStrategy(
        strategies=[
            SMAPriceStrategy(50),
            SMAPriceStrategy(200),
            MomentumStrategy(63),
        ],
        mode="MAJORITY",
        label="Combo_MAJ_50SMA_200SMA_MOM63",
    ))

    # 7. Close > 200 SMA AND MACD bullish AND RSI(14) > 30 (triple filter)
    strategies.append(ComboStrategy(
        strategies=[
            SMAPriceStrategy(200),
            MACDStrategy(12, 26, 9),
            RSIThresholdStrategy(14, 30),
        ],
        mode="AND",
        label="Combo_200SMA_AND_MACD_AND_RSI30",
    ))

    # 8. 12-month momentum > 0 AND 200 SMA slope positive (20-day)
    strategies.append(ComboStrategy(
        strategies=[
            MomentumStrategy(252),
            SMASlopeStrategy(200, 20),
        ],
        mode="AND",
        label="Combo_MOM252_AND_200SMA_Slope20",
    ))

    # ══════════════════════════════════════════════════════════════════
    # ROUND 2: Extensive combination testing based on Round 1 results
    # Best building blocks: RSI_14_above_30, SMA_Cross_20_50,
    #   MACD_8_17_9, SMA-200, SMA-50, MOM-5, MOM-63
    # ══════════════════════════════════════════════════════════════════

    # ── RSI as primary filter combos ──
    # RSI is the top signal for FTSE100, Nifty, and near-top for SP500/STOXX

    # 9. RSI > 30 AND SMA_Cross_20_50 (two best signals combined)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), SMACrossoverStrategy(20, 50)],
        mode="AND", label="C_RSI30_AND_SMACross2050",
    ))

    # 10. RSI > 30 OR SMA_Cross_20_50 (either bullish signal)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), SMACrossoverStrategy(20, 50)],
        mode="OR", label="C_RSI30_OR_SMACross2050",
    ))

    # 11. RSI > 30 AND Close > 200 SMA (RSI + long-term trend)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), SMAPriceStrategy(200)],
        mode="AND", label="C_RSI30_AND_200SMA",
    ))

    # 12. RSI > 30 AND Close > 50 SMA (RSI + medium-term trend)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), SMAPriceStrategy(50)],
        mode="AND", label="C_RSI30_AND_50SMA",
    ))

    # 13. RSI > 30 AND MACD(8,17,9) bullish (two momentum signals)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9)],
        mode="AND", label="C_RSI30_AND_MACD817",
    ))

    # 14. RSI > 30 AND 5-day momentum > 0 (RSI + short-term momentum)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MomentumStrategy(5)],
        mode="AND", label="C_RSI30_AND_MOM5",
    ))

    # 15. RSI > 30 AND 63-day momentum > 0 (RSI + medium-term momentum)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MomentumStrategy(63)],
        mode="AND", label="C_RSI30_AND_MOM63",
    ))

    # 16. RSI > 30 AND 21-day momentum > 0 (RSI + 1-month momentum)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MomentumStrategy(21)],
        mode="AND", label="C_RSI30_AND_MOM21",
    ))

    # ── SMA Crossover as primary filter combos ──

    # 17. SMA_Cross_20_50 AND Close > 200 SMA (crossover + long-term trend)
    strategies.append(ComboStrategy(
        strategies=[SMACrossoverStrategy(20, 50), SMAPriceStrategy(200)],
        mode="AND", label="C_SMACross2050_AND_200SMA",
    ))

    # 18. SMA_Cross_20_50 AND MACD(8,17,9) (crossover + MACD momentum)
    strategies.append(ComboStrategy(
        strategies=[SMACrossoverStrategy(20, 50), MACDStrategy(8, 17, 9)],
        mode="AND", label="C_SMACross2050_AND_MACD817",
    ))

    # 19. SMA_Cross_20_50 AND 63-day momentum > 0
    strategies.append(ComboStrategy(
        strategies=[SMACrossoverStrategy(20, 50), MomentumStrategy(63)],
        mode="AND", label="C_SMACross2050_AND_MOM63",
    ))

    # 20. SMA_Cross_20_50 OR RSI > 30 (relaxed — invest if either says yes)
    # Duplicate of #10 with different name for clarity — skip

    # ── MACD as primary filter combos ──

    # 21. MACD(8,17,9) AND Close > 200 SMA
    strategies.append(ComboStrategy(
        strategies=[MACDStrategy(8, 17, 9), SMAPriceStrategy(200)],
        mode="AND", label="C_MACD817_AND_200SMA",
    ))

    # 22. MACD(8,17,9) AND Close > 50 SMA
    strategies.append(ComboStrategy(
        strategies=[MACDStrategy(8, 17, 9), SMAPriceStrategy(50)],
        mode="AND", label="C_MACD817_AND_50SMA",
    ))

    # 23. MACD(8,17,9) OR RSI > 30 (either momentum signal)
    strategies.append(ComboStrategy(
        strategies=[MACDStrategy(8, 17, 9), RSIThresholdStrategy(14, 30)],
        mode="OR", label="C_MACD817_OR_RSI30",
    ))

    # 24. MACD(8,17,9) AND RSI > 30 AND Close > 50 SMA (triple filter)
    strategies.append(ComboStrategy(
        strategies=[MACDStrategy(8, 17, 9), RSIThresholdStrategy(14, 30), SMAPriceStrategy(50)],
        mode="AND", label="C_MACD817_RSI30_AND_50SMA",
    ))

    # ── Trend + Slope combos ──

    # 25. Close > 50 SMA AND 50 SMA slope positive (10-day)
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(50), SMASlopeStrategy(50, 10)],
        mode="AND", label="C_50SMA_AND_50SMA_Slope10",
    ))

    # 26. Close > 50 SMA AND 50 SMA slope positive (20-day)
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(50), SMASlopeStrategy(50, 20)],
        mode="AND", label="C_50SMA_AND_50SMA_Slope20",
    ))

    # 27. Close > 200 SMA AND 200 SMA slope positive (20-day)
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(200), SMASlopeStrategy(200, 20)],
        mode="AND", label="C_200SMA_AND_200SMA_Slope20",
    ))

    # 28. RSI > 30 AND 200 SMA slope positive (20-day)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), SMASlopeStrategy(200, 20)],
        mode="AND", label="C_RSI30_AND_200SMA_Slope20",
    ))

    # ── RSI threshold variations ──

    # 29. RSI > 35 (slightly stricter than 30)
    strategies.append(RSIThresholdStrategy(period=14, threshold=35))

    # 30. RSI > 40 (moderate threshold)
    strategies.append(RSIThresholdStrategy(period=14, threshold=40))

    # 31. RSI > 25 (more permissive)
    strategies.append(RSIThresholdStrategy(period=14, threshold=25))

    # 32. RSI > 50 (above midline = bullish bias)
    strategies.append(RSIThresholdStrategy(period=14, threshold=50))

    # 33. RSI(21) > 30 (slower RSI)
    strategies.append(RSIThresholdStrategy(period=21, threshold=30))

    # ── RSI threshold combos ──

    # 34. RSI > 35 AND SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 35), SMACrossoverStrategy(20, 50)],
        mode="AND", label="C_RSI35_AND_SMACross2050",
    ))

    # 35. RSI > 50 AND Close > 200 SMA (RSI above midline + long-term trend)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 50), SMAPriceStrategy(200)],
        mode="AND", label="C_RSI50_AND_200SMA",
    ))

    # 36. RSI > 40 AND Close > 50 SMA
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 40), SMAPriceStrategy(50)],
        mode="AND", label="C_RSI40_AND_50SMA",
    ))

    # ── Multi-signal MAJORITY combos ──

    # 37. MAJORITY: RSI>30, Close>50SMA, Close>200SMA (any 2 of 3)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), SMAPriceStrategy(50), SMAPriceStrategy(200)],
        mode="MAJORITY", label="C_MAJ_RSI30_50SMA_200SMA",
    ))

    # 38. MAJORITY: RSI>30, MACD(8,17,9), SMA_Cross_20_50 (any 2 of 3)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="C_MAJ_RSI30_MACD817_Cross2050",
    ))

    # 39. MAJORITY: RSI>30, MOM-63, Close>200SMA (any 2 of 3)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MomentumStrategy(63), SMAPriceStrategy(200)],
        mode="MAJORITY", label="C_MAJ_RSI30_MOM63_200SMA",
    ))

    # ── Defensive combos (try to minimize drawdown) ──

    # 40. Close > 200 SMA AND RSI > 30 AND MACD(8,17,9) (triple strict)
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(200), RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9)],
        mode="AND", label="C_200SMA_RSI30_AND_MACD817",
    ))

    # 41. Close > 50 SMA AND Close > 200 SMA AND RSI > 30 (triple trend+RSI)
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(50), SMAPriceStrategy(200), RSIThresholdStrategy(14, 30)],
        mode="AND", label="C_50SMA_200SMA_AND_RSI30",
    ))

    # 42. Close > 200 SMA AND 200 SMA slope(20) positive AND RSI > 30
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(200), SMASlopeStrategy(200, 20), RSIThresholdStrategy(14, 30)],
        mode="AND", label="C_200SMA_200SMASlope20_AND_RSI30",
    ))

    # ── Aggressive combos (try to capture more upside) ──

    # 43. Close > 50 SMA OR RSI > 30 (invest if either medium-term trend or not oversold)
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(50), RSIThresholdStrategy(14, 30)],
        mode="OR", label="C_50SMA_OR_RSI30",
    ))

    # 44. Close > 200 SMA OR RSI > 30 (invest if either long-term trend or not oversold)
    strategies.append(ComboStrategy(
        strategies=[SMAPriceStrategy(200), RSIThresholdStrategy(14, 30)],
        mode="OR", label="C_200SMA_OR_RSI30",
    ))

    # 45. SMA_Cross_20_50 OR Close > 200 SMA (invest if crossover or long-term uptrend)
    strategies.append(ComboStrategy(
        strategies=[SMACrossoverStrategy(20, 50), SMAPriceStrategy(200)],
        mode="OR", label="C_SMACross2050_OR_200SMA",
    ))

    # 46. MOM-5 > 0 OR RSI > 30 (short-momentum or not-oversold)
    strategies.append(ComboStrategy(
        strategies=[MomentumStrategy(5), RSIThresholdStrategy(14, 30)],
        mode="OR", label="C_MOM5_OR_RSI30",
    ))

    # 47. MOM-63 > 0 OR SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[MomentumStrategy(63), SMACrossoverStrategy(20, 50)],
        mode="OR", label="C_MOM63_OR_SMACross2050",
    ))

    # ── SMA crossover variations ──

    # 48. SMA Cross 10/30 (faster crossover)
    strategies.append(SMACrossoverStrategy(10, 30))

    # 49. SMA Cross 20/100 (medium crossover)
    strategies.append(SMACrossoverStrategy(20, 100))

    # 50. SMA Cross 10/30 AND RSI > 30
    strategies.append(ComboStrategy(
        strategies=[SMACrossoverStrategy(10, 30), RSIThresholdStrategy(14, 30)],
        mode="AND", label="C_SMACross1030_AND_RSI30",
    ))

    # 51. SMA Cross 10/30 AND Close > 200 SMA
    strategies.append(ComboStrategy(
        strategies=[SMACrossoverStrategy(10, 30), SMAPriceStrategy(200)],
        mode="AND", label="C_SMACross1030_AND_200SMA",
    ))

    # ── More RSI combos with MACD ──

    # 52. RSI > 40 AND MACD(8,17,9) (stricter RSI + fast MACD)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 40), MACDStrategy(8, 17, 9)],
        mode="AND", label="C_RSI40_AND_MACD817",
    ))

    # 53. RSI > 35 AND MACD(8,17,9) AND Close > 50 SMA
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 35), MACDStrategy(8, 17, 9), SMAPriceStrategy(50)],
        mode="AND", label="C_RSI35_MACD817_AND_50SMA",
    ))

    # 54. RSI > 30 AND MACD(12,26,9) AND Close > 200 SMA
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(12, 26, 9), SMAPriceStrategy(200)],
        mode="AND", label="C_RSI30_MACD1226_AND_200SMA",
    ))

    # ── 4-signal combos ──

    # 55. MAJORITY of 4: RSI>30, Close>50SMA, Close>200SMA, MACD(8,17,9)
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), SMAPriceStrategy(50),
            SMAPriceStrategy(200), MACDStrategy(8, 17, 9),
        ],
        mode="MAJORITY", label="C_MAJ4_RSI30_50SMA_200SMA_MACD817",
    ))

    # 56. MAJORITY of 4: RSI>30, SMA_Cross_20_50, MOM-63, MACD(8,17,9)
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), SMACrossoverStrategy(20, 50),
            MomentumStrategy(63), MACDStrategy(8, 17, 9),
        ],
        mode="MAJORITY", label="C_MAJ4_RSI30_Cross2050_MOM63_MACD817",
    ))

    # ── Momentum-based combos ──

    # 57. MOM-21 > 0 AND RSI > 30
    strategies.append(ComboStrategy(
        strategies=[MomentumStrategy(21), RSIThresholdStrategy(14, 30)],
        mode="AND", label="C_MOM21_AND_RSI30",
    ))

    # 58. MOM-63 > 0 AND Close > 50 SMA
    strategies.append(ComboStrategy(
        strategies=[MomentumStrategy(63), SMAPriceStrategy(50)],
        mode="AND", label="C_MOM63_AND_50SMA",
    ))

    # 59. MOM-63 > 0 AND RSI > 30 AND Close > 200 SMA
    strategies.append(ComboStrategy(
        strategies=[MomentumStrategy(63), RSIThresholdStrategy(14, 30), SMAPriceStrategy(200)],
        mode="AND", label="C_MOM63_RSI30_AND_200SMA",
    ))

    # 60. MOM-126 > 0 OR SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[MomentumStrategy(126), SMACrossoverStrategy(20, 50)],
        mode="OR", label="C_MOM126_OR_SMACross2050",
    ))

    # ══════════════════════════════════════════════════════════════════
    # ROUND 3: Build on champion C_MAJ_RSI30_MACD817_Cross2050
    # It uses MAJORITY(RSI>30, MACD817, Cross2050).
    # Test variations: different RSI thresholds, MACD variants,
    # add 4th/5th signals, try AND/OR variants of the same 3.
    # ══════════════════════════════════════════════════════════════════

    # ── Champion variants with different RSI thresholds ──

    # 61. MAJORITY: RSI>25, MACD(8,17,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 25), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI25_MACD817_Cross2050",
    ))

    # 62. MAJORITY: RSI>35, MACD(8,17,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 35), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI35_MACD817_Cross2050",
    ))

    # 63. MAJORITY: RSI>40, MACD(8,17,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 40), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI40_MACD817_Cross2050",
    ))

    # 64. MAJORITY: RSI(21)>30, MACD(8,17,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(21, 30), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI21_30_MACD817_Cross2050",
    ))

    # ── Champion variants with different MACD ──

    # 65. MAJORITY: RSI>30, MACD(12,26,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(12, 26, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MACD1226_Cross2050",
    ))

    # 66. MAJORITY: RSI>30, MACD(19,39,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(19, 39, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MACD1939_Cross2050",
    ))

    # ── Champion variants: AND instead of MAJORITY ──

    # 67. AND: RSI>30, MACD(8,17,9), SMA_Cross_20_50 (all 3 must agree)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="AND", label="R3_AND_RSI30_MACD817_Cross2050",
    ))

    # 68. OR: RSI>30, MACD(8,17,9), SMA_Cross_20_50 (any 1 of 3)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="OR", label="R3_OR_RSI30_MACD817_Cross2050",
    ))

    # ── Champion + 4th signal (MAJORITY of 4) ──

    # 69. MAJ4: RSI>30, MACD(8,17,9), Cross_20_50, Close>200SMA
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), SMAPriceStrategy(200),
        ],
        mode="MAJORITY", label="R3_MAJ4_RSI30_MACD817_Cross2050_200SMA",
    ))

    # 70. MAJ4: RSI>30, MACD(8,17,9), Cross_20_50, Close>50SMA
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), SMAPriceStrategy(50),
        ],
        mode="MAJORITY", label="R3_MAJ4_RSI30_MACD817_Cross2050_50SMA",
    ))

    # 71. MAJ4: RSI>30, MACD(8,17,9), Cross_20_50, MOM-63
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), MomentumStrategy(63),
        ],
        mode="MAJORITY", label="R3_MAJ4_RSI30_MACD817_Cross2050_MOM63",
    ))

    # 72. MAJ4: RSI>30, MACD(8,17,9), Cross_20_50, 200SMA_slope20
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), SMASlopeStrategy(200, 20),
        ],
        mode="MAJORITY", label="R3_MAJ4_RSI30_MACD817_Cross2050_200SMASlp20",
    ))

    # ── Champion + 5th signal (MAJORITY of 5) ──

    # 73. MAJ5: RSI>30, MACD(8,17,9), Cross_20_50, Close>200SMA, MOM-63
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), SMAPriceStrategy(200),
            MomentumStrategy(63),
        ],
        mode="MAJORITY", label="R3_MAJ5_RSI30_MACD817_Cross2050_200SMA_MOM63",
    ))

    # 74. MAJ5: RSI>30, MACD(8,17,9), Cross_20_50, Close>50SMA, Close>200SMA
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), SMAPriceStrategy(50),
            SMAPriceStrategy(200),
        ],
        mode="MAJORITY", label="R3_MAJ5_RSI30_MACD817_Cross2050_50_200SMA",
    ))

    # ── Runner-up variants (RSI_14_above_25 was 2nd best) ──

    # 75. MAJORITY: RSI>25, MACD(8,17,9), Cross_20_50, Close>200SMA
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 25), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), SMAPriceStrategy(200),
        ],
        mode="MAJORITY", label="R3_MAJ4_RSI25_MACD817_Cross2050_200SMA",
    ))

    # ── RSI_25 based combos ──

    # 76. RSI > 25 AND SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 25), SMACrossoverStrategy(20, 50)],
        mode="AND", label="R3_RSI25_AND_Cross2050",
    ))

    # 77. RSI > 25 AND Close > 200 SMA
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 25), SMAPriceStrategy(200)],
        mode="AND", label="R3_RSI25_AND_200SMA",
    ))

    # 78. RSI > 25 OR MACD(8,17,9)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 25), MACDStrategy(8, 17, 9)],
        mode="OR", label="R3_RSI25_OR_MACD817",
    ))

    # ── Different crossover combos with champion's signals ──

    # 79. MAJORITY: RSI>30, MACD(8,17,9), SMA_Cross_10_30
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMACrossoverStrategy(10, 30)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MACD817_Cross1030",
    ))

    # 80. MAJORITY: RSI>30, MACD(8,17,9), Close>50SMA (instead of cross)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMAPriceStrategy(50)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MACD817_50SMA",
    ))

    # 81. MAJORITY: RSI>30, MACD(8,17,9), Close>200SMA (instead of cross)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMAPriceStrategy(200)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MACD817_200SMA",
    ))

    # ── RSI(21) variants of champion ──

    # 82. MAJORITY: RSI(21)>25, MACD(8,17,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(21, 25), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI21_25_MACD817_Cross2050",
    ))

    # 83. MAJORITY: RSI(21)>35, MACD(8,17,9), SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(21, 35), MACDStrategy(8, 17, 9), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI21_35_MACD817_Cross2050",
    ))

    # ── Momentum replacement in champion ──

    # 84. MAJORITY: RSI>30, MOM-63, SMA_Cross_20_50 (MACD replaced with MOM)
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MomentumStrategy(63), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MOM63_Cross2050",
    ))

    # 85. MAJORITY: RSI>30, MOM-21, SMA_Cross_20_50
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MomentumStrategy(21), SMACrossoverStrategy(20, 50)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MOM21_Cross2050",
    ))

    # ── Per-index optimized: test different combos that might favor different indices ──

    # 86. MAJORITY: RSI>30, MACD(8,17,9), SMA_Cross_20_50, MOM-126
    strategies.append(ComboStrategy(
        strategies=[
            RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9),
            SMACrossoverStrategy(20, 50), MomentumStrategy(126),
        ],
        mode="MAJORITY", label="R3_MAJ4_RSI30_MACD817_Cross2050_MOM126",
    ))

    # 87. MAJORITY: RSI>30, MACD(8,17,9), SMA_Slope_50_10
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMASlopeStrategy(50, 10)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MACD817_50SMASlp10",
    ))

    # 88. MAJORITY: RSI>30, MACD(8,17,9), SMA_Slope_50_20
    strategies.append(ComboStrategy(
        strategies=[RSIThresholdStrategy(14, 30), MACDStrategy(8, 17, 9), SMASlopeStrategy(50, 20)],
        mode="MAJORITY", label="R3_MAJ_RSI30_MACD817_50SMASlp20",
    ))

    return strategies


def get_strategy_by_name(name: str) -> Strategy | None:
    """Look up a strategy by its unique name."""
    for s in get_all_strategies():
        if s.name == name:
            return s
    return None
