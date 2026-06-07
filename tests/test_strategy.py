"""Multi-leg strategy engine: payoff, breakevens, max profit/loss, net Greeks.

All payoffs are net P&L at expiry on a per-share basis (multiplier defaults to
1) so the reference values below are hand-computable. Sign convention:
quantity is signed (+long / -short); entry_cost is a net debit when positive,
a net credit when negative.

Hand-computed reference cases drive the tests — the iron condor is the M3
acceptance gate (PLAN.md): breakevens [93, 107], max profit 2, max loss -3.
"""
import math

import numpy as np
import pytest

from lab.pricing import Greeks
from lab.pricing.black_scholes import delta as bs_delta
from lab.pricing.black_scholes import price as bs_price
from lab.strategy.legs import Leg, Strategy
from lab.strategy.presets import (
    calendar,
    covered_call,
    iron_condor,
    straddle,
    strangle,
    vertical_spread,
)

T = 0.5  # common expiry (years) for single-expiry structures


# --- Single long call: the simplest payoff ------------------------------

def _long_call():
    return Strategy([Leg("call", quantity=1, strike=100.0, premium=5.0, expiry=T)])


def test_long_call_payoff_points():
    s = _long_call()
    assert s.payoff(100.0) == pytest.approx(-5.0)  # max loss = premium paid
    assert s.payoff(105.0) == pytest.approx(0.0)   # breakeven
    assert s.payoff(110.0) == pytest.approx(5.0)


def test_long_call_breakeven_and_extrema():
    s = _long_call()
    assert s.breakevens() == pytest.approx([105.0])
    assert s.max_loss() == pytest.approx(-5.0)
    assert math.isinf(s.max_profit()) and s.max_profit() > 0


def test_payoff_is_vectorized():
    s = _long_call()
    out = s.payoff(np.array([100.0, 105.0, 110.0]))
    np.testing.assert_allclose(out, [-5.0, 0.0, 5.0])


# --- Naked short call: unbounded loss -----------------------------------

def test_naked_short_call_has_unbounded_loss():
    s = Strategy([Leg("call", quantity=-1, strike=100.0, premium=5.0, expiry=T)])
    assert s.max_profit() == pytest.approx(5.0)  # keep the premium
    assert math.isinf(s.max_loss()) and s.max_loss() < 0


# --- Entry cost sign convention -----------------------------------------

def test_entry_cost_debit_positive_credit_negative():
    debit = vertical_spread("call", 100.0, 110.0, 5.0, 2.0, expiry=T)  # bull call spread
    assert debit.entry_cost() == pytest.approx(3.0)
    credit = iron_condor(90.0, 95.0, 105.0, 110.0, 1.0, 2.0, 2.0, 1.0, expiry=T)
    assert credit.entry_cost() == pytest.approx(-2.0)


# --- Vertical (bull call) spread ----------------------------------------

def test_vertical_spread_metrics():
    s = vertical_spread("call", 100.0, 110.0, 5.0, 2.0, expiry=T)
    assert s.breakevens() == pytest.approx([103.0])
    assert s.max_profit() == pytest.approx(7.0)
    assert s.max_loss() == pytest.approx(-3.0)


# --- Iron condor (THE ACCEPTANCE GATE) ----------------------------------

def test_iron_condor_breakevens_and_max_loss():
    s = iron_condor(
        long_put_strike=90.0,
        short_put_strike=95.0,
        short_call_strike=105.0,
        long_call_strike=110.0,
        long_put_premium=1.0,
        short_put_premium=2.0,
        short_call_premium=2.0,
        long_call_premium=1.0,
        expiry=T,
    )
    assert s.breakevens() == pytest.approx([93.0, 107.0])
    assert s.max_profit() == pytest.approx(2.0)   # net credit kept
    assert s.max_loss() == pytest.approx(-3.0)    # width(5) - credit(2)


# --- Straddle / strangle ------------------------------------------------

def test_straddle_metrics():
    s = straddle(100.0, call_premium=5.0, put_premium=4.0, expiry=T)
    assert s.breakevens() == pytest.approx([91.0, 109.0])
    assert s.max_loss() == pytest.approx(-9.0)
    assert math.isinf(s.max_profit())


def test_strangle_metrics():
    s = strangle(call_strike=105.0, put_strike=95.0, call_premium=3.0, put_premium=3.0, expiry=T)
    assert s.breakevens() == pytest.approx([89.0, 111.0])
    assert s.max_loss() == pytest.approx(-6.0)


# --- Covered call (has a stock leg) -------------------------------------

def test_covered_call_metrics():
    s = covered_call(stock_entry=100.0, call_strike=105.0, call_premium=3.0, expiry=T)
    assert s.breakevens() == pytest.approx([97.0])      # entry - premium
    assert s.max_profit() == pytest.approx(8.0)         # (strike - entry) + premium
    assert s.max_loss() == pytest.approx(-97.0)         # stock to zero, less premium


# --- Net Greeks ----------------------------------------------------------

def test_net_greeks_of_single_call_match_bs():
    s = _long_call()
    g = s.net_greeks(S=100.0, r=0.05, sigma=0.2)
    assert isinstance(g, Greeks)
    assert g.delta == pytest.approx(bs_delta(100.0, 100.0, T, 0.05, 0.2, "call"))


def test_covered_call_net_delta_between_zero_and_one():
    s = covered_call(stock_entry=100.0, call_strike=105.0, call_premium=3.0, expiry=T)
    g = s.net_greeks(S=100.0, r=0.05, sigma=0.2)
    # long 1 share (delta 1) minus a short call's delta -> in (0, 1).
    assert 0.0 < g.delta < 1.0


# --- Mark-to-model (value before expiry) --------------------------------

def test_mark_to_model_single_call_is_bs_minus_premium():
    s = _long_call()
    mtm = s.mark_to_model(S=100.0, r=0.05, sigma=0.2)
    assert mtm == pytest.approx(bs_price(100.0, 100.0, T, 0.05, 0.2, "call") - 5.0)


# --- Probability of profit (lognormal) ----------------------------------

def test_prob_profit_of_long_stock_at_median_entry_is_half():
    # Entry at the lognormal median -> P(S_T > entry) = 0.5.
    S, r, sigma, q = 100.0, 0.05, 0.2, 0.0
    median = S * math.exp((r - q - 0.5 * sigma**2) * T)
    s = Strategy([Leg("stock", quantity=1, premium=median, expiry=T)])
    p = s.prob_profit(S=S, r=r, sigma=sigma, t=T, q=q)
    assert p == pytest.approx(0.5, abs=1e-6)


def test_prob_profit_is_a_probability():
    s = straddle(100.0, call_premium=5.0, put_premium=4.0, expiry=T)
    p = s.prob_profit(S=100.0, r=0.05, sigma=0.2, t=T)
    assert 0.0 <= p <= 1.0


# --- Calendar spread: multi-expiry, payoff() must refuse ----------------

def test_calendar_builds_two_legs_with_different_expiries():
    s = calendar(strike=100.0, kind="call", near_premium=3.0, far_premium=5.0,
                 near_expiry=0.25, far_expiry=0.75)
    assert len(s.legs) == 2
    assert {leg.expiry for leg in s.legs} == {0.25, 0.75}


def test_single_expiry_methods_reject_mixed_expiries():
    s = calendar(strike=100.0, kind="call", near_premium=3.0, far_premium=5.0,
                 near_expiry=0.25, far_expiry=0.75)
    with pytest.raises(ValueError):
        s.payoff(100.0)
    # ...but mark-to-model (which respects each leg's own expiry) works.
    mtm = s.mark_to_model(S=100.0, r=0.05, sigma=0.2)
    assert isinstance(mtm, float)


# --- Validation ----------------------------------------------------------

def test_unknown_leg_kind_raises():
    with pytest.raises(ValueError):
        Leg("banana", quantity=1, strike=100.0, expiry=T).payoff(100.0)
