"""Volatility-regime read and verdict, defined a priori.

The verdict targets short-premium strategies (selling vol), the portfolio's
representative case. The logic is fixed *before* any backtest, from volatility
first principles — not tuned to flatter a curve:

- **realized-vol percentile** — is option premium currently rich vs its own
  recent history? (high percentile = rich)
- **term-structure read** — proxied from the underlier alone as the ratio of
  short-window to long-window realized vol. > 1 means vol is *spiking*
  (backwardation, stress); < 1 means it's *calming* (contango).

Decision:
- **SIT_OUT** when vol is spiking (term_ratio high) or at a crisis percentile —
  exactly when short premium gets run over.
- **FAVORABLE** when premium is rich (high percentile) and *not* spiking.
- **NEUTRAL** otherwise.

SIT_OUT is the whole point: a curve-fitter never adds an output that reduces
trade count. The thresholds below are the a-priori knobs — change them in the
open, in source, not in response to results.
"""
from dataclasses import dataclass

import numpy as np

FAVORABLE = "favorable"
NEUTRAL = "neutral"
SIT_OUT = "sit_out"

# A-priori thresholds (set before fitting; defend these on the whiteboard).
SPIKE_RATIO = 1.20        # short/long realized-vol ratio above this = spiking
CRISIS_PERCENTILE = 0.95  # realized-vol percentile above this = crisis
RICH_PERCENTILE = 0.60    # premium considered "rich" at/above this percentile
CALM_RATIO = 1.10         # term ratio at/below this counts as "not spiking"

TRADING_DAYS = 252


@dataclass(frozen=True)
class RegimeRead:
    realized_vol: float   # annualized, short window, latest
    vol_percentile: float # 0..1, latest short-window vol vs its trailing history
    term_ratio: float     # short-window vol / long-window vol


def _log_returns(prices):
    prices = np.asarray(prices, dtype=float)
    return np.diff(np.log(prices))


def realized_vol(prices, window=21):
    """Annualized realized volatility over the last `window` log returns."""
    rets = _log_returns(prices)[-window:]
    if rets.size < 2:
        return 0.0
    return float(rets.std(ddof=1) * np.sqrt(TRADING_DAYS))


def _rolling_realized_vol(prices, window):
    """Realized vol ending at each day for which a full window exists."""
    rets = _log_returns(prices)
    if rets.size < window:
        return np.array([])
    out = np.empty(rets.size - window + 1)
    for i in range(out.size):
        out[i] = rets[i : i + window].std(ddof=1)
    return out * np.sqrt(TRADING_DAYS)


def regime_read(prices, short_window=21, long_window=63, percentile_lookback=TRADING_DAYS):
    short_vol = realized_vol(prices, short_window)
    long_vol = realized_vol(prices, long_window)
    term_ratio = short_vol / long_vol if long_vol > 0 else 1.0

    rolling = _rolling_realized_vol(prices, short_window)
    if rolling.size == 0:
        percentile = 0.0
    else:
        history = rolling[-percentile_lookback:]
        current = rolling[-1]
        # Fraction of trailing observations strictly below current.
        percentile = float((history < current).mean())

    return RegimeRead(realized_vol=short_vol, vol_percentile=percentile, term_ratio=term_ratio)


def verdict(read: RegimeRead):
    """Map a regime read to a short-premium verdict via the a-priori rule."""
    if read.term_ratio > SPIKE_RATIO or read.vol_percentile > CRISIS_PERCENTILE:
        return SIT_OUT
    if read.vol_percentile >= RICH_PERCENTILE and read.term_ratio <= CALM_RATIO:
        return FAVORABLE
    return NEUTRAL


def classify(prices, short_window=21, long_window=63, percentile_lookback=TRADING_DAYS):
    """Return (verdict, RegimeRead) for a price series."""
    read = regime_read(prices, short_window, long_window, percentile_lookback)
    return verdict(read), read
