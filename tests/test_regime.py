"""Volatility-regime filter — the judgment hook that can say "sit out".

The rule is defined *a priori* from volatility logic (realized-vol percentile
+ a short/long term-structure read), not tuned after a backtest. Its most
important output is SIT_OUT, which a curve-fitter would never add because it
reduces trade count. The M5 acceptance gate: the filter does say SIT_OUT on a
spiking/backwardated fixture.
"""
import numpy as np
import pytest

from lab.regime.vol_regime import FAVORABLE, NEUTRAL, SIT_OUT, classify, realized_vol, regime_read


def _prices(returns):
    return 100.0 * np.exp(np.cumsum(np.asarray(returns, dtype=float)))


def _alt(n, mag):
    """n alternating +mag/-mag daily log returns (clean, constant-vol)."""
    r = np.empty(n)
    r[0::2] = mag
    r[1::2] = -mag
    return r


# Fixtures with a-priori-known volatility character.
SPIKING = _prices(np.concatenate([_alt(300, 0.003), _alt(25, 0.06)]))      # recent vol blow-up
ELEVATED_CALM = _prices(np.concatenate([_alt(260, 0.003), _alt(70, 0.02)]))  # rich but stable
QUIET = _prices(_alt(330, 0.003))                                           # low vol throughout
CALMING = _prices(np.concatenate([_alt(300, 0.05), _alt(40, 0.003)]))       # vol falling recently


# --- realized vol --------------------------------------------------------

def test_realized_vol_is_zero_for_constant_return_series():
    prices = 100.0 * np.exp(np.cumsum(np.full(60, 0.001)))  # identical daily return
    assert realized_vol(prices, window=21) == pytest.approx(0.0, abs=1e-12)


def test_realized_vol_scales_with_swing_size():
    small = realized_vol(_prices(_alt(60, 0.01)), window=40)
    big = realized_vol(_prices(_alt(60, 0.02)), window=40)
    assert big == pytest.approx(2 * small, rel=1e-6)


# --- regime read (realized-vol percentile + term structure) -------------

def test_regime_read_fields_are_well_formed():
    read = regime_read(ELEVATED_CALM)
    assert read.realized_vol > 0.0
    assert 0.0 <= read.vol_percentile <= 1.0
    assert read.term_ratio > 0.0


def test_term_ratio_above_one_when_vol_is_spiking():
    assert regime_read(SPIKING).term_ratio > 1.2


def test_term_ratio_below_one_when_vol_is_calming():
    assert regime_read(CALMING).term_ratio < 1.0


def test_vol_percentile_high_when_recent_vol_exceeds_history():
    assert regime_read(ELEVATED_CALM).vol_percentile >= 0.6


def test_vol_percentile_low_for_constant_vol():
    assert regime_read(QUIET).vol_percentile < 0.6


# --- verdicts (a-priori thresholds) -------------------------------------

def test_spiking_regime_says_sit_out():
    # THE ACCEPTANCE GATE: the filter can and does say "sit out".
    verdict, _ = classify(SPIKING)
    assert verdict == SIT_OUT


def test_elevated_but_calm_regime_is_favorable_for_short_premium():
    verdict, _ = classify(ELEVATED_CALM)
    assert verdict == FAVORABLE


def test_quiet_regime_is_neutral():
    verdict, _ = classify(QUIET)
    assert verdict == NEUTRAL


def test_classify_returns_the_underlying_read():
    verdict, read = classify(SPIKING)
    assert verdict in (FAVORABLE, NEUTRAL, SIT_OUT)
    assert read.term_ratio == pytest.approx(regime_read(SPIKING).term_ratio)
