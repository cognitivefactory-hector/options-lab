"""Black-Scholes pricing + analytic Greeks — the crown-jewel quant core.

Golden invariants (per CLAUDE.md / PLAN.md M1): put-call parity holds within
tolerance, Greeks carry the correct signs, and ATM values land in the expected
ranges. Reference values use the canonical textbook case:

    S=100, K=100, t=1yr, r=5%, sigma=20%, q=0  ->  call=10.4506, put=5.5735

Conventions (raw analytic, documented so later layers scale them for display):
- vega is per 1.0 change in vol (i.e. per 100 vol-points), not per 1%.
- theta is per year, not per day.
- rho is per 1.0 change in the rate, not per 1%.
"""
import math

import pytest

from lab.pricing.black_scholes import delta, gamma, greeks, price, rho, theta, vega

# Canonical textbook case.
S, K, T, R, SIG = 100.0, 100.0, 1.0, 0.05, 0.20

CALL_REF = 10.450583572185565
PUT_REF = 5.573526022256971


# --- Price ---------------------------------------------------------------

def test_call_price_matches_textbook_value():
    assert price(S, K, T, R, SIG, "call") == pytest.approx(CALL_REF, abs=1e-9)


def test_put_price_matches_textbook_value():
    assert price(S, K, T, R, SIG, "put") == pytest.approx(PUT_REF, abs=1e-9)


def test_put_call_parity_holds():
    # C - P == S*e^{-qT} - K*e^{-rT}
    c = price(S, K, T, R, SIG, "call")
    p = price(S, K, T, R, SIG, "put")
    assert c - p == pytest.approx(S - K * math.exp(-R * T), abs=1e-10)


def test_unknown_option_kind_raises():
    with pytest.raises(ValueError):
        price(S, K, T, R, SIG, "banana")


def test_price_at_expiry_is_intrinsic_value():
    assert price(120, 100, 0.0, R, SIG, "call") == pytest.approx(20.0)
    assert price(80, 100, 0.0, R, SIG, "call") == pytest.approx(0.0)
    assert price(80, 100, 0.0, R, SIG, "put") == pytest.approx(20.0)


# --- Delta ---------------------------------------------------------------

def test_call_delta_in_unit_interval_put_delta_negative():
    assert 0.0 < delta(S, K, T, R, SIG, "call") < 1.0
    assert -1.0 < delta(S, K, T, R, SIG, "put") < 0.0


def test_call_and_put_delta_differ_by_one():
    # With q=0: delta_call - delta_put == 1.
    assert delta(S, K, T, R, SIG, "call") - delta(S, K, T, R, SIG, "put") == pytest.approx(1.0)


def test_deep_itm_call_delta_approaches_one():
    assert delta(1000, 100, T, R, SIG, "call") == pytest.approx(1.0, abs=1e-6)


def test_deep_otm_call_delta_approaches_zero():
    assert delta(10, 100, T, R, SIG, "call") == pytest.approx(0.0, abs=1e-6)


# --- Gamma / Vega (same for calls and puts) ------------------------------

def test_gamma_is_positive_and_kind_independent():
    g_call = gamma(S, K, T, R, SIG, "call")
    g_put = gamma(S, K, T, R, SIG, "put")
    assert g_call > 0.0
    assert g_call == pytest.approx(g_put)


def test_vega_is_positive_and_kind_independent():
    v_call = vega(S, K, T, R, SIG, "call")
    v_put = vega(S, K, T, R, SIG, "put")
    assert v_call > 0.0
    assert v_call == pytest.approx(v_put)


def test_vega_units_are_per_unit_vol():
    # Per 1.0 vol; ATM textbook case ~ 37.52.
    assert vega(S, K, T, R, SIG, "call") == pytest.approx(37.524, abs=1e-3)


# --- Theta / Rho ---------------------------------------------------------

def test_long_call_theta_is_negative():
    assert theta(S, K, T, R, SIG, "call") < 0.0


def test_call_rho_positive_put_rho_negative():
    assert rho(S, K, T, R, SIG, "call") > 0.0
    assert rho(S, K, T, R, SIG, "put") < 0.0


# --- Greeks bundle -------------------------------------------------------

def test_greeks_bundle_matches_individual_functions():
    g = greeks(S, K, T, R, SIG, "call")
    assert g.delta == pytest.approx(delta(S, K, T, R, SIG, "call"))
    assert g.gamma == pytest.approx(gamma(S, K, T, R, SIG, "call"))
    assert g.theta == pytest.approx(theta(S, K, T, R, SIG, "call"))
    assert g.vega == pytest.approx(vega(S, K, T, R, SIG, "call"))
    assert g.rho == pytest.approx(rho(S, K, T, R, SIG, "call"))


def test_dividend_yield_lowers_call_raises_put():
    # A positive dividend yield reduces the forward -> cheaper call, richer put.
    assert price(S, K, T, R, SIG, "call", q=0.03) < price(S, K, T, R, SIG, "call")
    assert price(S, K, T, R, SIG, "put", q=0.03) > price(S, K, T, R, SIG, "put")
