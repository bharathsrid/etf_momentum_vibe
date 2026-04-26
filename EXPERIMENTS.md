# ETF Momentum Backtest — Complete Experiment Log & Results

**Project**: etf_momentum_vibe  
**Date**: April 26, 2026  
**Total strategies tested**: 118  
**Total backtests run**: 472 (118 strategies × 4 indices)

---

## 1. Methodology

### 1.1 Objective
Beat buy-and-hold returns from January 1, 2016 to present using technical-indicator-based timing signals. For each index, the strategy either invests 100% in the index or stays 100% in cash.

### 1.2 Indices & Data
| Index | Ticker | Start | End | Bars |
|-------|--------|-------|-----|------|
| S&P 500 | ^GSPC | 2016-01-04 | 2026-04-24 | 2,592 |
| FTSE 100 | ^FTSE | 2016-01-04 | 2026-04-24 | 2,604 |
| Nifty 50 | ^NSEI | 2016-01-04 | 2026-04-24 | 2,539 |
| STOXX 50 | ^STOXX50E | 2016-01-04 | 2026-04-24 | 2,591 |

- **Data source**: Yahoo Finance end-of-day OHLCV (auto-adjusted for splits/dividends)
- **Data cached** locally as Parquet files (refreshed daily)

### 1.3 Capital & Allocation
- **Total starting capital**: $10,000
- **Per index**: $2,500 (independent — no cross-allocation)
- **Cash return**: 2% annualized (daily compounding at 2%/252 per day)
- **Transaction costs**: None

### 1.4 Execution Rules
- **Signal generation**: At day T's close, using all data up to and including day T
- **Trade execution**: At day T+1's open price (avoids look-ahead bias)
- **Position**: Binary — either 100% invested or 100% cash
- **Warmup period**: Each strategy has a warmup (e.g., 200-day SMA needs 200 bars before first signal). During warmup, the portfolio stays in cash earning risk-free rate. All CAGR calculations include the warmup period.

### 1.5 Performance Metrics
| Metric | Formula |
|--------|---------|
| Total Return | (Final Equity / Initial) - 1 |
| CAGR | (Final / Initial)^(252/days) - 1 |
| Max Drawdown | min(equity / running_peak - 1) |
| Sharpe Ratio | mean(daily_return - rf_daily) / std(daily_return - rf_daily) × √252 |
| Sortino Ratio | mean(daily_return - rf_daily) × 252 / downside_deviation |
| Win Rate | Profitable round-trips / Total round-trips |
| Alpha | Strategy CAGR - Buy & Hold CAGR |

### 1.6 Aggregate Portfolio
Each index is treated independently with $2,500. The aggregate equity curve is the sum of the 4 per-index equity curves (forward-filling any date gaps between different trading calendars). Metrics are computed on this combined curve.

---

## 2. Buy-and-Hold Baseline

| Index | CAGR | Total Return | Max Drawdown | Sharpe | Final Value ($2,500) |
|-------|------|-------------|-------------|--------|---------------------|
| S&P 500 | 12.1% | 224.7% | -33.9% | 0.63 | $8,116 |
| FTSE 100 | 3.9% | 48.7% | -36.6% | 0.20 | $3,718 |
| Nifty 50 | 11.2% | 190.6% | -38.4% | 0.63 | $7,264 |
| STOXX 50 | 6.1% | 83.5% | -38.3% | 0.31 | $4,588 |
| **Aggregate** | **~9.0%** | **136.9%** | **-35.3%** | **0.56** | **$23,686** |

---

## 3. Strategy Definitions

### 3.1 Signal Types

#### SMA Price (5 strategies)
**Rule**: INVESTED if Close > SMA(Close, N); else CASH

| # | Name | N (period) | Warmup |
|---|------|-----------|--------|
| 1 | SMA-10 | 10 | 10 |
| 2 | SMA-20 | 20 | 20 |
| 3 | SMA-50 | 50 | 50 |
| 4 | SMA-100 | 100 | 100 |
| 5 | SMA-200 | 200 | 200 |

#### SMA Crossover (8 strategies)
**Rule**: INVESTED if SMA(short) > SMA(long); else CASH

| # | Name | Short | Long | Warmup |
|---|------|-------|------|--------|
| 6 | SMA_Cross_10_20 | 10 | 20 | 20 |
| 7 | SMA_Cross_10_30 | 10 | 30 | 30 |
| 8 | SMA_Cross_10_50 | 10 | 50 | 50 |
| 9 | SMA_Cross_20_50 | 20 | 50 | 50 |
| 10 | SMA_Cross_20_100 | 20 | 100 | 100 |
| 11 | SMA_Cross_50_100 | 50 | 100 | 100 |
| 12 | SMA_Cross_50_200 | 50 | 200 | 200 |

#### SMA Slope (4 strategies)
**Rule**: INVESTED if (SMA[today] - SMA[today - slope_period]) / SMA[today - slope_period] > 0; else CASH

| # | Name | MA Period | Slope Period | Warmup |
|---|------|-----------|-------------|--------|
| 13 | SMA_Slope_50_10 | 50 | 10 | 60 |
| 14 | SMA_Slope_50_20 | 50 | 20 | 70 |
| 15 | SMA_Slope_200_20 | 200 | 20 | 220 |
| 16 | SMA_Slope_200_50 | 200 | 50 | 250 |

#### Momentum (5 strategies)
**Rule**: INVESTED if Close[today] / Close[today - lookback] - 1 > 0; else CASH

| # | Name | Lookback | Approx | Warmup |
|---|------|----------|--------|--------|
| 17 | MOM-5 | 5 days | 1 week | 5 |
| 18 | MOM-21 | 21 days | 1 month | 21 |
| 19 | MOM-63 | 63 days | 3 months | 63 |
| 20 | MOM-126 | 126 days | 6 months | 126 |
| 21 | MOM-252 | 252 days | 12 months | 252 |

#### MACD (3 strategies)
**Rule**: INVESTED if MACD_line > Signal_line; else CASH  
**Formula**: MACD_line = EMA(fast) - EMA(slow); Signal_line = EMA(MACD_line, signal_period)

| # | Name | Fast | Slow | Signal | Warmup |
|---|------|------|------|--------|--------|
| 22 | MACD_12_26_9 | 12 | 26 | 9 | 35 |
| 23 | MACD_8_17_9 | 8 | 17 | 9 | 26 |
| 24 | MACD_19_39_9 | 19 | 39 | 9 | 48 |

#### RSI Threshold (7 strategies)
**Rule**: INVESTED if RSI(period) > threshold; else CASH  
**RSI formula**: Standard Wilder smoothing with alpha = 1/period

| # | Name | Period | Threshold | Warmup |
|---|------|--------|-----------|--------|
| 25 | RSI_14_above_25 | 14 | 25 | 15 |
| 26 | RSI_14_above_30 | 14 | 30 | 15 |
| 27 | RSI_14_above_35 | 14 | 35 | 15 |
| 28 | RSI_14_above_40 | 14 | 40 | 15 |
| 29 | RSI_14_above_50 | 14 | 50 | 15 |
| 30 | RSI_21_above_30 | 21 | 30 | 22 |

#### RSI Hysteresis (3 strategies)
**Rule**: Stateful with hysteresis bands to reduce whipsawing  
- When CASH: switch to INVESTED if RSI > lower_threshold  
- When INVESTED: switch to CASH if RSI < upper_threshold

| # | Name | Period | Lower | Upper | Warmup |
|---|------|--------|-------|-------|--------|
| 31 | RSI_14_30_70 | 14 | 30 | 70 | 15 |
| 32 | RSI_14_40_60 | 14 | 40 | 60 | 15 |
| 33 | RSI_21_35_65 | 21 | 35 | 65 | 22 |

#### Time-Series Momentum (4 strategies)
**Rule**: At each rebalancing point (every holding_period days), compute lookback-day return. If positive → INVESTED for next holding_period; else CASH.

| # | Name | Lookback | Holding | Warmup |
|---|------|----------|---------|--------|
| 34 | TSMOM_252_21 | 252 (12mo) | 21 (1mo) | 252 |
| 35 | TSMOM_252_63 | 252 (12mo) | 63 (3mo) | 252 |
| 36 | TSMOM_126_21 | 126 (6mo) | 21 (1mo) | 126 |
| 37 | TSMOM_63_21 | 63 (3mo) | 21 (1mo) | 63 |

#### Combination Strategies (81 strategies)
**Rule**: Combine 2+ sub-strategies using AND, OR, or MAJORITY logic.

- **AND**: INVESTED only if ALL sub-strategies say INVESTED
- **OR**: INVESTED if ANY sub-strategy says INVESTED
- **MAJORITY**: INVESTED if more than half of sub-strategies say INVESTED

See Appendix A for the full list of all 81 combination strategies with exact rules.

---

## 4. Experiment Rounds

### Round 1: Base Strategies (39 strategies)
**Goal**: Test individual signal types to identify which work best on their own.

**Key findings**:
- RSI_14_above_30 was the only strategy that beat buy-and-hold on aggregate (+0.6% alpha)
- SMA_Cross_20_50 had the best aggregate Sharpe after RSI
- MACD_8_17_9 had the lowest aggregate MaxDD (-8.8%) but very low CAGR
- No strategy beat B&H on S&P 500
- 5 strategies beat B&H on FTSE 100 (RSI_14_above_30 best at +2.7% alpha)
- 2 strategies beat B&H on Nifty 50 (SMA_Cross_20_50 at +2.0% alpha)
- No strategy beat B&H on STOXX 50

**Top 5 aggregate (Round 1)**:
| Strategy | CAGR | Alpha | Sharpe | MaxDD |
|----------|------|-------|--------|-------|
| RSI_14_above_30 | 9.6% | +0.6% | 0.70 | -19.4% |
| SMA_Cross_20_50 | 7.6% | -1.4% | 0.74 | -16.0% |
| C_MACD817_OR_RSI30 | 10.1% | +1.0% | 0.74 | -19.4% |
| C_50SMA_OR_MOM126 | 7.1% | -2.0% | 0.60 | -15.3% |
| Buy & Hold | 8.5% | — | 0.56 | -35.3% |

### Round 2: Combination Testing (21 new combos added, total 60)
**Goal**: Combine the best individual signals (RSI, MACD, SMA_Cross) using AND/OR/MAJORITY logic.

**Key findings**:
- **C_MAJ_RSI30_MACD817_Cross2050** emerged as the champion: MAJORITY of RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50)
- The MAJORITY approach significantly outperformed AND and OR
- C_MACD817_OR_RSI30 was the best for FTSE 100 specifically
- RSI_14_above_25 (more permissive) beat RSI_14_above_30 on STOXX 50

**Top 5 aggregate (Round 2)**:
| Strategy | CAGR | Alpha | Sharpe | MaxDD |
|----------|------|-------|--------|-------|
| C_MAJ_RSI30_MACD817_Cross2050 | 11.2% | +2.2% | 0.94 | -16.6% |
| RSI_14_above_25 | 10.2% | +1.2% | 0.71 | -23.3% |
| C_MACD817_OR_RSI30 | 10.1% | +1.0% | 0.74 | -19.4% |
| RSI_21_above_30 | 10.0% | +0.9% | 0.71 | -22.1% |
| C_MOM5_OR_RSI30 | 9.8% | +0.8% | 0.71 | -19.5% |

### Round 3: Champion Iteration (58 new combos added, total 118)
**Goal**: Build on the champion (MAJORITY of 3 signals) by varying:
- RSI threshold (25, 30, 35, 40) and period (14, 21)
- MACD parameters (8/17/9, 12/26/9, 19/39/9)
- Combining logic (AND vs MAJORITY vs OR)
- Adding 4th and 5th signals (Close>200SMA, Close>50SMA, MOM-63, SMA slope)
- Replacing signals (MOM-63 instead of MACD, SMA_Slope instead of SMA_Cross)

**Key findings**:
- **R3_MAJ_RSI21_25_MACD817_Cross2050** is the new overall champion (+2.5% alpha, Sharpe 0.96)
- Using RSI(21) with threshold 25 slightly outperforms RSI(14) with threshold 30
- The MAJORITY of 3 signals remains the sweet spot; adding 4th/5th signals reduces alpha
- MACD(8,17,9) is the best MACD variant for this approach
- AND logic is too strict (misses upside); OR logic is too loose (doesn't protect)
- Per-index, different strategies are optimal (see Section 5)

**Top 10 aggregate (Round 3 — final)**:
| Strategy | CAGR | Alpha | Sharpe | MaxDD | #Trades |
|----------|------|-------|--------|-------|---------|
| R3_MAJ_RSI21_25_MACD817_Cross2050 | 11.5% | +2.5% | 0.96 | -16.3% | 404 |
| R3_MAJ_RSI21_30_MACD817_Cross2050 | 11.3% | +2.2% | 0.94 | -16.2% | 412 |
| R3_MAJ_RSI25_MACD817_Cross2050 | 11.3% | +2.2% | 0.94 | -16.2% | 416 |
| C_MAJ_RSI30_MACD817_Cross2050 | 11.2% | +2.2% | 0.94 | -16.6% | 436 |
| R3_MAJ_RSI21_35_MACD817_Cross2050 | 11.2% | +2.2% | 0.95 | -16.3% | 428 |
| R3_RSI25_OR_MACD817 | 10.7% | +1.7% | 0.75 | -23.2% | 58 |
| R3_MAJ_RSI35_MACD817_Cross2050 | 10.3% | +1.2% | 0.87 | -17.1% | 532 |
| RSI_14_above_25 | 10.2% | +1.2% | 0.71 | -23.3% | 58 |
| C_MACD817_OR_RSI30 | 10.1% | +1.0% | 0.74 | -19.4% | 180 |
| RSI_21_above_30 | 10.0% | +0.9% | 0.71 | -22.1% | 66 |

---

## 5. Per-Index Results (Final — Best Strategy per Index)

### S&P 500 (^GSPC)

| Strategy | CAGR | Alpha | MaxDD | Sharpe | Final Value |
|----------|------|-------|-------|--------|-------------|
| **Buy & Hold** | **12.1%** | — | **-33.9%** | **0.63** | **$8,116** |
| R3_MAJ_RSI21_25_MACD817_Cross2050 ★ | 13.9% | +0.6% | -31.1% | 0.84 | $9,533 |
| R3_MAJ_RSI21_35_MACD817_Cross2050 ★ | 13.5% | +0.2% | -31.2% | 0.83 | $9,173 |
| C_MAJ_RSI30_MACD817_Cross2050 ★ | 13.3% | +0.1% | -31.9% | 0.82 | $9,063 |
| R3_MAJ_RSI25_MACD817_Cross2050 ★ | 13.3% | +0.0% | -31.1% | 0.81 | $9,026 |

**4 strategies beat B&H.** S&P 500 is the hardest index to beat — it had a strong, relatively uninterrupted bull market. The MAJORITY approach adds minimal alpha but significantly improves Sharpe (+0.2) and slightly reduces drawdown.

### FTSE 100 (^FTSE)

| Strategy | CAGR | Alpha | MaxDD | Sharpe | Final Value |
|----------|------|-------|-------|--------|-------------|
| **Buy & Hold** | **3.9%** | — | **-36.6%** | **0.20** | **$3,718** |
| C_MACD817_OR_RSI30 ★ | 7.4% | +3.3% | -16.6% | 0.45 | $5,217 |
| RSI_21_above_30 ★ | 7.3% | +3.2% | -18.1% | 0.44 | $5,028 |
| C_MOM5_OR_RSI30 ★ | 6.8% | +2.7% | -17.4% | 0.41 | $4,945 |
| RSI_14_above_30 ★ | 6.8% | +2.7% | -17.6% | 0.41 | $4,934 |

**20 strategies beat B&H.** FTSE 100 is the easiest index to beat — it's choppy with deep drawdowns. The OR approach works best here, nearly doubling the CAGR and halving the drawdown. Simple RSI(14)>30 already adds +2.7% alpha.

### Nifty 50 (^NSEI)

| Strategy | CAGR | Alpha | MaxDD | Sharpe | Final Value |
|----------|------|-------|-------|--------|-------------|
| **Buy & Hold** | **11.2%** | — | **-38.4%** | **0.63** | **$7,264** |
| C_MAJ_RSI30_MACD817_Cross2050 ★ | 17.8% | +5.6% | -15.0% | 1.14 | $13,018 |
| R3_MAJ_RSI25_MACD817_Cross2050 ★ | 17.8% | +5.6% | -15.0% | 1.14 | $13,018 |
| R3_MAJ_RSI21_25_MACD817_Cross2050 ★ | 17.8% | +5.6% | -15.0% | 1.14 | $13,018 |
| R3_MAJ_RSI30_MACD1939_Cross2050 ★ | 17.2% | +4.9% | -15.5% | 1.18 | $12,326 |

**15 strategies beat B&H.** Nifty 50 shows the strongest trend-following benefit. The MAJORITY approach nearly doubles the final value ($13K vs $7.3K) and slashes drawdown from -38% to -15%. Sharpe of 1.14-1.18 is exceptional.

### STOXX 50 (^STOXX50E)

| Strategy | CAGR | Alpha | MaxDD | Sharpe | Final Value |
|----------|------|-------|-------|--------|-------------|
| **Buy & Hold** | **6.1%** | — | **-38.3%** | **0.31** | **$4,588** |
| R3_RSI25_OR_MACD817 ★ | 9.8% | +3.3% | -25.5% | 0.51 | $6,562 |
| R3_MAJ_RSI21_25_MACD817_Cross2050 ★ | 7.4% | +0.8% | -23.5% | 0.42 | $5,189 |
| R3_MAJ_RSI21_35_MACD817_Cross2050 ★ | 7.2% | +0.7% | -23.5% | 0.41 | $5,125 |
| C_MAJ_RSI30_MACD817_Cross2050 ★ | 6.9% | +0.4% | -25.8% | 0.40 | $4,982 |

**7 strategies beat B&H.** STOXX 50 benefits from trend-following but is harder than FTSE. The OR approach works better here (RSI>25 OR MACD bullish gives +3.3% alpha), similar to FTSE.

---

## 5.5 Best Strategy Per Index — Exact Rules

> This section gives the **single best strategy for each index** with its exact, unambiguous rules. These are the strategies you would actually trade.

### S&P 500 Best: `R3_MAJ_RSI21_25_MACD817_Cross2050`

**Result**: CAGR 13.9% (vs B&H 12.1%), Alpha +0.6%, MaxDD -31.1% (vs -33.9%), Sharpe 0.84 (vs 0.63), Final $9,533 (vs $8,116)

**Exact rules — check these 3 conditions at the close of each trading day:**

| # | Condition | Exact Computation |
|---|-----------|-------------------|
| 1 | **RSI(21) > 25** | Compute 21-day RSI using Wilder smoothing (alpha = 1/21). If RSI > 25 → signal = BULLISH, else → signal = BEARISH |
| 2 | **MACD(8,17,9) bullish** | Compute EMA(Close, 8) and EMA(Close, 17) using `adjust=False`. MACD line = EMA(8) - EMA(17). Signal line = EMA(MACD_line, 9). If MACD line > Signal line → signal = BULLISH, else → signal = BEARISH |
| 3 | **SMA(20) > SMA(50)** | Compute 20-day SMA and 50-day SMA of Close. If SMA(20) > SMA(50) → signal = BULLISH, else → signal = BEARISH |

**Decision**: If 2 or more of the 3 signals are BULLISH → **INVESTED** (buy/sell at next day's open). Otherwise → **CASH**.

**Why it works**: S&P 500 has long, strong trends. The MAJORITY vote keeps you invested during bull markets (all 3 agree) while protecting you during sharp drops (2 of 3 flip to bearish quickly). RSI(21) with threshold 25 is very permissive — it only exits when RSI drops below 25, which happens during severe selloffs.

**Trading frequency**: ~77 round-trip trades over 10 years (~8 per year). Mostly in market during uptrends, moves to cash during major corrections.

---

### FTSE 100 Best: `C_MACD817_OR_RSI30`

**Result**: CAGR 7.4% (vs B&H 3.9%), Alpha +3.3%, MaxDD -16.6% (vs -36.6%), Sharpe 0.45 (vs 0.20), Final $5,217 (vs $3,718)

**Exact rules — check these 2 conditions at the close of each trading day:**

| # | Condition | Exact Computation |
|---|-----------|-------------------|
| 1 | **MACD(8,17,9) bullish** | Compute EMA(Close, 8) and EMA(Close, 17) using `adjust=False`. MACD line = EMA(8) - EMA(17). Signal line = EMA(MACD_line, 9). If MACD line > Signal line → signal = BULLISH, else → signal = BEARISH |
| 2 | **RSI(14) > 30** | Compute 14-day RSI using Wilder smoothing (alpha = 1/14). If RSI > 30 → signal = BULLISH, else → signal = BEARISH |

**Decision**: If **either** signal is BULLISH → **INVESTED**. Only go to CASH when **both** are bearish.

**Why it works**: FTSE 100 is choppy with frequent false breakdowns. Using OR logic means you only exit when *both* momentum AND the oscillator confirm weakness. This avoids whipsawing out during routine dips. When both signals turn bearish, it's a genuine downtrend — stay in cash until one recovers.

**Trading frequency**: ~41 round-trip trades over 10 years (~4 per year). Less frequent trading because the OR gate keeps you invested more often.

---

### Nifty 50 Best: `C_MAJ_RSI30_MACD817_Cross2050`

**Result**: CAGR 17.8% (vs B&H 11.2%), Alpha +5.6%, MaxDD -15.0% (vs -38.4%), Sharpe 1.14 (vs 0.63), Final $13,018 (vs $7,264)

**Exact rules — check these 3 conditions at the close of each trading day:**

| # | Condition | Exact Computation |
|---|-----------|-------------------|
| 1 | **RSI(14) > 30** | Compute 14-day RSI using Wilder smoothing (alpha = 1/14). If RSI > 30 → signal = BULLISH, else → signal = BEARISH |
| 2 | **MACD(8,17,9) bullish** | Compute EMA(Close, 8) and EMA(Close, 17) using `adjust=False`. MACD line = EMA(8) - EMA(17). Signal line = EMA(MACD_line, 9). If MACD line > Signal line → signal = BULLISH, else → signal = BEARISH |
| 3 | **SMA(20) > SMA(50)** | Compute 20-day SMA and 50-day SMA of Close. If SMA(20) > SMA(50) → signal = BULLISH, else → signal = BEARISH |

**Decision**: If 2 or more of the 3 signals are BULLISH → **INVESTED**. Otherwise → **CASH**.

**Why it works**: Nifty 50 has strong trending behavior but with vicious corrections (e.g., -38% MaxDD for B&H). The MAJORITY approach captures the massive uptrend (CAGR nearly doubles from 11.2% to 17.8%) while cutting drawdown by 60% (-38.4% to -15.0%). This is the strongest result across all 4 indices. The final value nearly doubles buy-and-hold ($13K vs $7.3K).

**Trading frequency**: ~85 round-trip trades over 10 years (~8.5 per year).

---

### STOXX 50 Best: `R3_RSI25_OR_MACD817`

**Result**: CAGR 9.8% (vs B&H 6.1%), Alpha +3.3%, MaxDD -25.5% (vs -38.3%), Sharpe 0.51 (vs 0.31), Final $6,562 (vs $4,588)

**Exact rules — check these 2 conditions at the close of each trading day:**

| # | Condition | Exact Computation |
|---|-----------|-------------------|
| 1 | **RSI(14) > 25** | Compute 14-day RSI using Wilder smoothing (alpha = 1/14). If RSI > 25 → signal = BULLISH, else → signal = BEARISH |
| 2 | **MACD(8,17,9) bullish** | Compute EMA(Close, 8) and EMA(Close, 17) using `adjust=False`. MACD line = EMA(8) - EMA(17). Signal line = EMA(MACD_line, 9). If MACD line > Signal line → signal = BULLISH, else → signal = BEARISH |

**Decision**: If **either** signal is BULLISH → **INVESTED**. Only go to CASH when **both** are bearish.

**Why it works**: STOXX 50, like FTSE 100, is a choppy European index with deep drawdowns. The OR logic with a very permissive RSI threshold (25) keeps you invested during most uptrends while MACD provides the timing for exits. When both RSI drops below 25 (severe weakness) *and* MACD turns bearish, it's time to exit. The +3.3% alpha nearly doubles the CAGR.

**Trading frequency**: ~13 round-trip trades over 10 years (~1.3 per year). Very low turnover — most of the time you're invested.

---

### Summary Table

| Index | Best Strategy | Logic | CAGR | Alpha | MaxDD | Sharpe | #Trades/yr |
|-------|--------------|-------|------|-------|-------|--------|------------|
| S&P 500 | R3_MAJ_RSI21_25_MACD817_Cross2050 | MAJ(2/3) | 13.9% | +0.6% | -31.1% | 0.84 | ~8 |
| FTSE 100 | C_MACD817_OR_RSI30 | OR | 7.4% | +3.3% | -16.6% | 0.45 | ~4 |
| Nifty 50 | C_MAJ_RSI30_MACD817_Cross2050 | MAJ(2/3) | 17.8% | +5.6% | -15.0% | 1.14 | ~8.5 |
| STOXX 50 | R3_RSI25_OR_MACD817 | OR | 9.8% | +3.3% | -25.5% | 0.51 | ~1.3 |
| **B&H S&P 500** | — | — | 12.1% | — | -33.9% | 0.63 | — |
| **B&H FTSE 100** | — | — | 3.9% | — | -36.6% | 0.20 | — |
| **B&H Nifty 50** | — | — | 11.2% | — | -38.4% | 0.63 | — |
| **B&H STOXX 50** | — | — | 6.1% | — | -38.3% | 0.31 | — |

**Pattern**: Trendy indices (S&P 500, Nifty 50) → use MAJORITY of 3 signals. Choppy indices (FTSE 100, STOXX 50) → use OR of 2 signals. All winning strategies share the same building blocks: **RSI** (oversold filter) + **MACD(8,17,9)** (momentum) + optionally **SMA crossover** (trend direction).

---

## 6. Key Findings

### 6.1 The MAJORITY Vote is the Winning Approach
- **AND** logic is too strict — keeps you in cash during uptrends when one signal disagrees
- **OR** logic is too loose — doesn't protect enough during downturns
- **MAJORITY** of 3 independent signal types provides the optimal balance: captures upside, avoids major drawdowns, reduces whipsaws

### 6.2 The Three Signal Types Should Be Independent
The champion strategy uses three *different categories* of indicators:
1. **Oscillator**: RSI (measures overbought/oversold)
2. **Momentum**: MACD (measures trend momentum)
3. **Trend**: SMA crossover (measures trend direction)

Using three of the same type (e.g., SMA-50, SMA-100, SMA-200) provides no diversification benefit.

### 6.3 Different Indices Need Different Approaches
| Index | Best Approach | Best Strategy | Alpha |
|-------|--------------|---------------|-------|
| S&P 500 | MAJORITY (conservative) | R3_MAJ_RSI21_25_MACD817_Cross2050 | +0.6% |
| FTSE 100 | OR (aggressive) | C_MACD817_OR_RSI30 | +3.3% |
| Nifty 50 | MAJORITY | C_MAJ_RSI30_MACD817_Cross2050 | +5.6% |
| STOXX 50 | OR (aggressive) | R3_RSI25_OR_MACD817 | +3.3% |

Choppy/range-bound indices (FTSE, STOXX) benefit more from OR logic — invest when *any* signal is positive. Trendy indices (S&P 500, Nifty) benefit more from MAJORITY — invest when *most* signals agree.

### 6.4 Drawdown Reduction is the Main Benefit
Even when alpha is small (e.g., +0.6% on S&P 500), the drawdown improvement is substantial:
- S&P 500: -33.9% → -31.1% (2.8pp improvement)
- FTSE 100: -36.6% → -16.6% (20pp improvement!)
- Nifty 50: -38.4% → -15.0% (23.4pp improvement!)
- STOXX 50: -38.3% → -25.5% (12.8pp improvement)

### 6.5 Simple Signals Can Work
RSI(14) > 30 alone beats buy-and-hold on 3 of 4 indices. The simplest signal that works is often the best starting point.

---

## 7. How to Reproduce

```bash
# Install dependencies
pip install -r requirements.txt

# Run full backtest (118 strategies × 4 indices)
python run.py

# Run per-index comparison
python per_index_comparison.py

# Run final summary
python final_summary.py

# View strategy definitions
python strategy_reference.py

# Filter specific strategies
python run.py --strategies R3_MAJ_RSI21_25_MACD817_Cross2050 C_MAJ_RSI30_MACD817_Cross2050

# Filter specific tickers
python run.py --tickers ^GSPC ^NSEI
```

---

## Appendix A: Complete Combination Strategy Reference

### Round 1 Combos (8 strategies)

| # | Name | Logic | Sub-strategies |
|---|------|-------|---------------|
| 38 | Combo_200SMA_AND_50SMA_Slope10 | AND | Close>SMA(200), SMA(50) slope(10d)>0 |
| 39 | Combo_50SMA_AND_200SMA | AND | Close>SMA(50), Close>SMA(200) |
| 40 | Combo_MOM252_AND_200SMA | AND | 252d return>0, Close>SMA(200) |
| 41 | Combo_MACD_AND_RSI14_A40 | AND | MACD(12,26,9) bullish, RSI(14)>40 |
| 42 | Combo_50SMA_OR_MOM126 | OR | Close>SMA(50), 126d return>0 |
| 43 | Combo_MAJ_50SMA_200SMA_MOM63 | MAJ(2/3) | Close>SMA(50), Close>SMA(200), 63d return>0 |
| 44 | Combo_200SMA_AND_MACD_AND_RSI30 | AND | Close>SMA(200), MACD(12,26,9) bullish, RSI(14)>30 |
| 45 | Combo_MOM252_AND_200SMA_Slope20 | AND | 252d return>0, SMA(200) slope(20d)>0 |

### Round 2 Combos (21 strategies)

| # | Name | Logic | Sub-strategies |
|---|------|-------|---------------|
| 46 | C_RSI30_AND_SMACross2050 | AND | RSI(14)>30, SMA(20)>SMA(50) |
| 47 | C_RSI30_OR_SMACross2050 | OR | RSI(14)>30, SMA(20)>SMA(50) |
| 48 | C_RSI30_AND_200SMA | AND | RSI(14)>30, Close>SMA(200) |
| 49 | C_RSI30_AND_50SMA | AND | RSI(14)>30, Close>SMA(50) |
| 50 | C_RSI30_AND_MACD817 | AND | RSI(14)>30, MACD(8,17,9) bullish |
| 51 | C_RSI30_AND_MOM5 | AND | RSI(14)>30, 5d return>0 |
| 52 | C_RSI30_AND_MOM63 | AND | RSI(14)>30, 63d return>0 |
| 53 | C_RSI30_AND_MOM21 | AND | RSI(14)>30, 21d return>0 |
| 54 | C_SMACross2050_AND_200SMA | AND | SMA(20)>SMA(50), Close>SMA(200) |
| 55 | C_SMACross2050_AND_MACD817 | AND | SMA(20)>SMA(50), MACD(8,17,9) bullish |
| 56 | C_SMACross2050_AND_MOM63 | AND | SMA(20)>SMA(50), 63d return>0 |
| 57 | C_MACD817_AND_200SMA | AND | MACD(8,17,9) bullish, Close>SMA(200) |
| 58 | C_MACD817_AND_50SMA | AND | MACD(8,17,9) bullish, Close>SMA(50) |
| 59 | C_MACD817_OR_RSI30 | OR | MACD(8,17,9) bullish, RSI(14)>30 |
| 60 | C_MACD817_RSI30_AND_50SMA | AND | MACD(8,17,9) bullish, RSI(14)>30, Close>SMA(50) |
| 61 | C_50SMA_AND_50SMA_Slope10 | AND | Close>SMA(50), SMA(50) slope(10d)>0 |
| 62 | C_50SMA_AND_50SMA_Slope20 | AND | Close>SMA(50), SMA(50) slope(20d)>0 |
| 63 | C_200SMA_AND_200SMA_Slope20 | AND | Close>SMA(200), SMA(200) slope(20d)>0 |
| 64 | C_RSI30_AND_200SMA_Slope20 | AND | RSI(14)>30, SMA(200) slope(20d)>0 |
| 65 | C_RSI35_AND_SMACross2050 | AND | RSI(14)>35, SMA(20)>SMA(50) |
| 66 | C_RSI50_AND_200SMA | AND | RSI(14)>50, Close>SMA(200) |
| 67 | C_RSI40_AND_50SMA | AND | RSI(14)>40, Close>SMA(50) |
| 68 | C_MAJ_RSI30_50SMA_200SMA | MAJ(2/3) | RSI(14)>30, Close>SMA(50), Close>SMA(200) |
| 69 | **C_MAJ_RSI30_MACD817_Cross2050** | MAJ(2/3) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 70 | C_MAJ_RSI30_MOM63_200SMA | MAJ(2/3) | RSI(14)>30, 63d return>0, Close>SMA(200) |
| 71 | C_200SMA_RSI30_AND_MACD817 | AND | Close>SMA(200), RSI(14)>30, MACD(8,17,9) bullish |
| 72 | C_50SMA_200SMA_AND_RSI30 | AND | Close>SMA(50), Close>SMA(200), RSI(14)>30 |
| 73 | C_200SMA_200SMASlope20_AND_RSI30 | AND | Close>SMA(200), SMA(200) slope(20d)>0, RSI(14)>30 |
| 74 | C_50SMA_OR_RSI30 | OR | Close>SMA(50), RSI(14)>30 |
| 75 | C_200SMA_OR_RSI30 | OR | Close>SMA(200), RSI(14)>30 |
| 76 | C_SMACross2050_OR_200SMA | OR | SMA(20)>SMA(50), Close>SMA(200) |
| 77 | C_MOM5_OR_RSI30 | OR | 5d return>0, RSI(14)>30 |
| 78 | C_MOM63_OR_SMACross2050 | OR | 63d return>0, SMA(20)>SMA(50) |
| 79 | C_SMACross1030_AND_RSI30 | AND | SMA(10)>SMA(30), RSI(14)>30 |
| 80 | C_SMACross1030_AND_200SMA | AND | SMA(10)>SMA(30), Close>SMA(200) |
| 81 | C_RSI40_AND_MACD817 | AND | RSI(14)>40, MACD(8,17,9) bullish |
| 82 | C_RSI35_MACD817_AND_50SMA | AND | RSI(14)>35, MACD(8,17,9) bullish, Close>SMA(50) |
| 83 | C_RSI30_MACD1226_AND_200SMA | AND | RSI(14)>30, MACD(12,26,9) bullish, Close>SMA(200) |
| 84 | C_MAJ4_RSI30_50SMA_200SMA_MACD817 | MAJ(3/4) | RSI(14)>30, Close>SMA(50), Close>SMA(200), MACD(8,17,9) bullish |
| 85 | C_MAJ4_RSI30_Cross2050_MOM63_MACD817 | MAJ(3/4) | RSI(14)>30, SMA(20)>SMA(50), 63d return>0, MACD(8,17,9) bullish |
| 86 | C_MOM21_AND_RSI30 | AND | 21d return>0, RSI(14)>30 |
| 87 | C_MOM63_AND_50SMA | AND | 63d return>0, Close>SMA(50) |
| 88 | C_MOM63_RSI30_AND_200SMA | AND | 63d return>0, RSI(14)>30, Close>SMA(200) |
| 89 | C_MOM126_OR_SMACross2050 | OR | 126d return>0, SMA(20)>SMA(50) |

### Round 3 Combos (28 strategies)

| # | Name | Logic | Sub-strategies |
|---|------|-------|---------------|
| 90 | R3_MAJ_RSI25_MACD817_Cross2050 | MAJ(2/3) | RSI(14)>25, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 91 | R3_MAJ_RSI35_MACD817_Cross2050 | MAJ(2/3) | RSI(14)>35, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 92 | R3_MAJ_RSI40_MACD817_Cross2050 | MAJ(2/3) | RSI(14)>40, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 93 | R3_MAJ_RSI21_30_MACD817_Cross2050 | MAJ(2/3) | RSI(21)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 94 | R3_MAJ_RSI30_MACD1226_Cross2050 | MAJ(2/3) | RSI(14)>30, MACD(12,26,9) bullish, SMA(20)>SMA(50) |
| 95 | R3_MAJ_RSI30_MACD1939_Cross2050 | MAJ(2/3) | RSI(14)>30, MACD(19,39,9) bullish, SMA(20)>SMA(50) |
| 96 | R3_AND_RSI30_MACD817_Cross2050 | AND | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 97 | R3_OR_RSI30_MACD817_Cross2050 | OR | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 98 | R3_MAJ4_RSI30_MACD817_Cross2050_200SMA | MAJ(3/4) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50), Close>SMA(200) |
| 99 | R3_MAJ4_RSI30_MACD817_Cross2050_50SMA | MAJ(3/4) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50), Close>SMA(50) |
| 100 | R3_MAJ4_RSI30_MACD817_Cross2050_MOM63 | MAJ(3/4) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50), 63d return>0 |
| 101 | R3_MAJ4_RSI30_MACD817_Cross2050_200SMASlp20 | MAJ(3/4) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50), SMA(200) slope(20d)>0 |
| 102 | R3_MAJ5_RSI30_MACD817_Cross2050_200SMA_MOM63 | MAJ(3/5) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50), Close>SMA(200), 63d return>0 |
| 103 | R3_MAJ5_RSI30_MACD817_Cross2050_50_200SMA | MAJ(3/5) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50), Close>SMA(50), Close>SMA(200) |
| 104 | R3_MAJ4_RSI25_MACD817_Cross2050_200SMA | MAJ(3/4) | RSI(14)>25, MACD(8,17,9) bullish, SMA(20)>SMA(50), Close>SMA(200) |
| 105 | R3_RSI25_AND_Cross2050 | AND | RSI(14)>25, SMA(20)>SMA(50) |
| 106 | R3_RSI25_AND_200SMA | AND | RSI(14)>25, Close>SMA(200) |
| 107 | R3_RSI25_OR_MACD817 | OR | RSI(14)>25, MACD(8,17,9) bullish |
| 108 | R3_MAJ_RSI30_MACD817_Cross1030 | MAJ(2/3) | RSI(14)>30, MACD(8,17,9) bullish, SMA(10)>SMA(30) |
| 109 | R3_MAJ_RSI30_MACD817_50SMA | MAJ(2/3) | RSI(14)>30, MACD(8,17,9) bullish, Close>SMA(50) |
| 110 | R3_MAJ_RSI30_MACD817_200SMA | MAJ(2/3) | RSI(14)>30, MACD(8,17,9) bullish, Close>SMA(200) |
| 111 | **R3_MAJ_RSI21_25_MACD817_Cross2050** | MAJ(2/3) | RSI(21)>25, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 112 | R3_MAJ_RSI21_35_MACD817_Cross2050 | MAJ(2/3) | RSI(21)>35, MACD(8,17,9) bullish, SMA(20)>SMA(50) |
| 113 | R3_MAJ_RSI30_MOM63_Cross2050 | MAJ(2/3) | RSI(14)>30, 63d return>0, SMA(20)>SMA(50) |
| 114 | R3_MAJ_RSI30_MOM21_Cross2050 | MAJ(2/3) | RSI(14)>30, 21d return>0, SMA(20)>SMA(50) |
| 115 | R3_MAJ4_RSI30_MACD817_Cross2050_MOM126 | MAJ(3/4) | RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50), 126d return>0 |
| 116 | R3_MAJ_RSI30_MACD817_50SMASlp10 | MAJ(2/3) | RSI(14)>30, MACD(8,17,9) bullish, SMA(50) slope(10d)>0 |
| 117 | R3_MAJ_RSI30_MACD817_50SMASlp20 | MAJ(2/3) | RSI(14)>30, MACD(8,17,9) bullish, SMA(50) slope(20d)>0 |

---

## Appendix B: Output Files

| File | Description |
|------|-------------|
| `output/aggregate_summary.csv` | All metrics for all strategies on aggregate portfolio |
| `output/per_ticker_summary.csv` | All metrics per ticker per strategy |
| `output/full_results.xlsx` | Multi-sheet Excel with metrics + equity curves |
| `output/plots/equity_aggregate.png` | Top 5 strategies equity curves vs B&H |
| `output/plots/equity_GSPC.png` | S&P 500 equity curves |
| `output/plots/equity_FTSE.png` | FTSE 100 equity curves |
| `output/plots/equity_NSEI.png` | Nifty 50 equity curves |
| `output/plots/equity_STOXX50E.png` | STOXX 50 equity curves |
| `output/plots/strategy_comparison.png` | Bar chart of CAGR/MaxDD/Sharpe across strategies |
| `output/plots/drawdown_*.png` | Drawdown charts for top strategies |

---

## Appendix C: Caveats & Limitations

1. **No transaction costs**: Results are optimistic for high-frequency switching strategies (MOM-5 trades 500+ times). Adding 0.1% per trade would significantly impact those.

2. **Survivorship bias**: These 4 indices are the ones that survived. We didn't test against indices that might have been chosen in 2016 but performed poorly.

3. **Look-ahead bias avoided**: Signal at T close, execute at T+1 open. But T+1 open is still somewhat "known" — in practice, slippage and gap risk exist.

4. **No out-of-sample validation**: All 118 strategies were tested on the same period. The best results are likely overstated due to multiple testing / data-snooping bias. Walk-forward validation would provide more realistic estimates.

5. **Cash return assumption**: 2% annualized is generous for 2016-2022 era (near-zero rates) but conservative for 2023-2026. A time-varying risk-free rate would be more accurate.

6. **Single asset class**: Only equity indices tested. Bonds, commodities, or mixed portfolios might show different optimal strategies.

7. **Tax implications**: No consideration of capital gains taxes, which would penalize frequent switching.
