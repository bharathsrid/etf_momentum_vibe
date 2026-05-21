"""End-of-day signal email for the 4 best-per-index ETF momentum strategies.

Triggered by EventBridge daily. Pulls the latest 18 months of OHLC from Yahoo,
computes the current signal for each strategy and a distance-to-flip estimate
for every sub-signal, then emails the report via SES.
"""

import os
from datetime import datetime, timezone

import boto3
import numpy as np
import pandas as pd
import yfinance as yf

SES_REGION = os.environ.get("AWS_REGION", "us-east-1")
FROM_ADDR = os.environ["SENDER_EMAIL"]
TO_ADDRS = [r.strip() for r in os.environ["RECIPIENTS"].split(",") if r.strip()]

TICKERS = {
    "^GSPC": "S&P 500",
    "^FTSE": "FTSE 100",
    "^NSEI": "Nifty 50",
    "^STOXX50E": "STOXX 50",
}

STRATEGIES = {
    "^GSPC": {
        "name": "R3_MAJ_RSI21_25_MACD817_Cross2050",
        "rule": "MAJORITY of 3: RSI(21)>25, MACD(8,17,9) bullish, SMA(20)>SMA(50)",
        "sub": [
            {"kind": "rsi",   "period": 21, "threshold": 25},
            {"kind": "macd",  "fast": 8,  "slow": 17, "signal": 9},
            {"kind": "cross", "short": 20, "long": 50},
        ],
        "logic": "MAJORITY",
    },
    "^FTSE": {
        "name": "C_MACD817_OR_RSI30",
        "rule": "OR of 2: MACD(8,17,9) bullish, RSI(14)>30",
        "sub": [
            {"kind": "macd", "fast": 8, "slow": 17, "signal": 9},
            {"kind": "rsi",  "period": 14, "threshold": 30},
        ],
        "logic": "OR",
    },
    "^NSEI": {
        "name": "C_MAJ_RSI30_MACD817_Cross2050",
        "rule": "MAJORITY of 3: RSI(14)>30, MACD(8,17,9) bullish, SMA(20)>SMA(50)",
        "sub": [
            {"kind": "rsi",   "period": 14, "threshold": 30},
            {"kind": "macd",  "fast": 8,  "slow": 17, "signal": 9},
            {"kind": "cross", "short": 20, "long": 50},
        ],
        "logic": "MAJORITY",
    },
    "^STOXX50E": {
        "name": "R3_RSI25_OR_MACD817",
        "rule": "OR of 2: RSI(14)>25, MACD(8,17,9) bullish",
        "sub": [
            {"kind": "rsi",  "period": 14, "threshold": 25},
            {"kind": "macd", "fast": 8,  "slow": 17, "signal": 9},
        ],
        "logic": "OR",
    },
}


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def _evaluate_sub(sub: dict, close: pd.Series) -> dict:
    """Return dict with bullish, label, distance description, and pct_to_flip."""
    if sub["kind"] == "rsi":
        rsi = _rsi(close, sub["period"])
        cur = float(rsi.iloc[-1])
        thr = sub["threshold"]
        bullish = cur > thr
        gap = cur - thr
        return {
            "label": f"RSI({sub['period']})>{thr}",
            "bullish": bullish,
            "value": f"RSI={cur:.1f}",
            "distance": f"{gap:+.1f} pts vs threshold {thr}",
            "flip_hint": _rsi_flip_hint(rsi, thr),
        }

    if sub["kind"] == "macd":
        ema_f = close.ewm(span=sub["fast"], adjust=False).mean()
        ema_s = close.ewm(span=sub["slow"], adjust=False).mean()
        macd = ema_f - ema_s
        sig = macd.ewm(span=sub["signal"], adjust=False).mean()
        diff = macd - sig
        cur_diff = float(diff.iloc[-1])
        bullish = cur_diff > 0
        # Magnitude in percent of price for context
        last_price = float(close.iloc[-1])
        pct_of_price = (cur_diff / last_price) * 100 if last_price else 0.0
        # Recent histogram swing as a sense of volatility
        recent_abs = float(diff.tail(60).abs().mean())
        rel_to_recent = (cur_diff / recent_abs) if recent_abs else 0.0
        return {
            "label": f"MACD({sub['fast']},{sub['slow']},{sub['signal']})>0",
            "bullish": bullish,
            "value": f"hist={cur_diff:+.4f} ({pct_of_price:+.3f}% of price)",
            "distance": f"{rel_to_recent:+.2f}× recent |hist| (60d avg |hist|={recent_abs:.4f})",
            "flip_hint": _macd_flip_hint(diff),
        }

    if sub["kind"] == "cross":
        s = close.rolling(sub["short"]).mean()
        l = close.rolling(sub["long"]).mean()
        cur_s = float(s.iloc[-1])
        cur_l = float(l.iloc[-1])
        bullish = cur_s > cur_l
        gap_pct = (cur_s - cur_l) / cur_l * 100 if cur_l else 0.0
        return {
            "label": f"SMA({sub['short']})>SMA({sub['long']})",
            "bullish": bullish,
            "value": f"SMA{sub['short']}={cur_s:.2f}, SMA{sub['long']}={cur_l:.2f}",
            "distance": f"{gap_pct:+.2f}% gap (short vs long)",
            "flip_hint": _cross_flip_hint(s, l),
        }

    raise ValueError(f"Unknown sub kind: {sub['kind']}")


def _rsi_flip_hint(rsi: pd.Series, thr: float) -> str:
    cur = float(rsi.iloc[-1])
    side = "above" if cur > thr else "below"
    # Days since last cross of the threshold
    state = rsi > thr
    flips = state != state.shift(1)
    last_flip = state.index[flips.fillna(False)][-1] if flips.any() else None
    days_since = (state.index[-1] - last_flip).days if last_flip is not None else None
    extra = f"; last crossed {days_since}d ago" if days_since is not None else ""
    return f"currently {side}{extra}"


def _macd_flip_hint(diff: pd.Series) -> str:
    state = diff > 0
    flips = state != state.shift(1)
    if not flips.any():
        return "no recent zero-line cross"
    last_flip = state.index[flips.fillna(False)][-1]
    days_since = (state.index[-1] - last_flip).days
    side = "bullish" if state.iloc[-1] else "bearish"
    return f"currently {side} for {days_since}d"


def _cross_flip_hint(short: pd.Series, long: pd.Series) -> str:
    state = short > long
    flips = state != state.shift(1)
    if not flips.any():
        return "no recent crossover"
    last_flip = state.index[flips.fillna(False)][-1]
    days_since = (state.index[-1] - last_flip).days
    side = "bullish (short>long)" if state.iloc[-1] else "bearish (short<long)"
    return f"currently {side} for {days_since}d"


def _combine(logic: str, bullish_flags: list[bool]) -> bool:
    if logic == "AND":
        return all(bullish_flags)
    if logic == "OR":
        return any(bullish_flags)
    if logic == "MAJORITY":
        return sum(bullish_flags) > len(bullish_flags) / 2
    raise ValueError(logic)


def _flips_required(logic: str, bullish_flags: list[bool]) -> int:
    """How many sub-signals would need to flip to change the overall decision."""
    n = len(bullish_flags)
    n_bull = sum(bullish_flags)
    invested = _combine(logic, bullish_flags)
    if logic == "AND":
        # Bullish only when n_bull == n. Becomes bearish when one flips.
        # Bearish: needs (n - n_bull) bullish flips to become bullish.
        return 1 if invested else (n - n_bull)
    if logic == "OR":
        # Bullish if n_bull >= 1. Bearish if 0.
        return n_bull if invested else 1
    if logic == "MAJORITY":
        needed_bull = n // 2 + 1
        if invested:
            return n_bull - needed_bull + 1  # how many bulls must flip to bearish
        return needed_bull - n_bull
    return 0


def fetch_data() -> dict[str, pd.DataFrame]:
    out = {}
    for tk in TICKERS:
        df = yf.download(tk, period="540d", auto_adjust=True, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df = df[["Open", "High", "Low", "Close", "Volume"]].ffill().dropna()
        out[tk] = df
    return out


def build_report() -> tuple[str, str]:
    data = fetch_data()
    rows_text = []
    rows_html = []

    for tk, friendly in TICKERS.items():
        cfg = STRATEGIES[tk]
        df = data[tk]
        last_date = df.index[-1].date()
        last_close = float(df["Close"].iloc[-1])

        sub_results = [_evaluate_sub(s, df["Close"]) for s in cfg["sub"]]
        bull_flags = [r["bullish"] for r in sub_results]
        invested = _combine(cfg["logic"], bull_flags)
        flips_to_change = _flips_required(cfg["logic"], bull_flags)
        state_label = "INVESTED" if invested else "CASH"
        flip_target = "CASH" if invested else "INVESTED"

        rows_text.append(
            f"\n{friendly} ({tk})  Close {last_date} = {last_close:,.2f}\n"
            f"  Strategy: {cfg['name']}\n"
            f"  Rule: {cfg['rule']}\n"
            f"  Decision: {state_label}\n"
            f"  Distance to flip: {flips_to_change} sub-signal(s) must change to switch to {flip_target}\n"
            f"  Sub-signals:"
        )
        for r in sub_results:
            mark = "BULL" if r["bullish"] else "BEAR"
            rows_text.append(
                f"    [{mark}] {r['label']:<22}  {r['value']}\n"
                f"           distance: {r['distance']}\n"
                f"           flip hint: {r['flip_hint']}"
            )

        rows_html.append(
            f"<h3 style='margin:18px 0 4px'>{friendly} <span style='color:#666;font-weight:normal'>({tk})</span> "
            f"&mdash; <b style='color:{'#0a7' if invested else '#a33'}'>{state_label}</b></h3>"
            f"<div style='font-size:13px;color:#555'>Close on {last_date} = {last_close:,.2f}</div>"
            f"<div style='font-size:13px'><b>Strategy:</b> {cfg['name']}</div>"
            f"<div style='font-size:13px'><b>Rule:</b> {cfg['rule']}</div>"
            f"<div style='font-size:13px'><b>Distance to flip:</b> {flips_to_change} sub-signal(s) must change to switch to {flip_target}</div>"
            "<table style='border-collapse:collapse;margin-top:6px;font-size:13px'>"
            "<tr style='background:#f0f0f0'>"
            "<th style='padding:4px 8px;text-align:left'>Signal</th>"
            "<th style='padding:4px 8px;text-align:left'>State</th>"
            "<th style='padding:4px 8px;text-align:left'>Value</th>"
            "<th style='padding:4px 8px;text-align:left'>Distance</th>"
            "<th style='padding:4px 8px;text-align:left'>Persistence</th>"
            "</tr>"
        )
        for r in sub_results:
            color = "#0a7" if r["bullish"] else "#a33"
            label = "BULL" if r["bullish"] else "BEAR"
            rows_html.append(
                f"<tr><td style='padding:4px 8px'>{r['label']}</td>"
                f"<td style='padding:4px 8px;color:{color};font-weight:bold'>{label}</td>"
                f"<td style='padding:4px 8px'>{r['value']}</td>"
                f"<td style='padding:4px 8px'>{r['distance']}</td>"
                f"<td style='padding:4px 8px'>{r['flip_hint']}</td></tr>"
            )
        rows_html.append("</table>")

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"ETF Momentum daily signal report  ({now_utc})\n"
        f"================================================\n"
        + "\n".join(rows_text)
        + "\n\nGenerated by Lambda. Strategies per EXPERIMENTS.md best-per-index.\n"
    )
    html = (
        f"<html><body style='font-family:Helvetica,Arial,sans-serif;max-width:780px'>"
        f"<h2 style='margin-bottom:0'>ETF Momentum &mdash; Daily Signal Report</h2>"
        f"<div style='color:#666;font-size:12px'>Generated {now_utc}</div>"
        + "".join(rows_html)
        + "<hr><div style='font-size:11px;color:#888'>Strategies per EXPERIMENTS.md best-per-index. "
        "Distance-to-flip counts how many sub-signals must change for the overall decision to switch.</div>"
        "</body></html>"
    )
    return text, html


def _verified_recipients(ses, candidates: list[str]) -> tuple[list[str], list[str]]:
    """Filter candidates against SES verified identities (needed in sandbox mode)."""
    attrs = ses.get_identity_verification_attributes(Identities=candidates).get(
        "VerificationAttributes", {}
    )
    verified, skipped = [], []
    for addr in candidates:
        if attrs.get(addr, {}).get("VerificationStatus") == "Success":
            verified.append(addr)
        else:
            skipped.append(addr)
    return verified, skipped


def lambda_handler(event, context):
    text, html = build_report()
    subject = f"ETF Momentum signals — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    ses = boto3.client("ses", region_name=SES_REGION)
    to_addrs, skipped = _verified_recipients(ses, TO_ADDRS)
    if not to_addrs:
        return {"status": "skipped", "reason": "no verified recipients", "skipped": skipped}
    resp = ses.send_email(
        Source=FROM_ADDR,
        Destination={"ToAddresses": to_addrs},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": text, "Charset": "UTF-8"},
                "Html": {"Data": html, "Charset": "UTF-8"},
            },
        },
    )
    return {
        "status": "ok",
        "message_id": resp.get("MessageId"),
        "to": to_addrs,
        "skipped": skipped,
    }


if __name__ == "__main__":
    print(build_report()[0])
