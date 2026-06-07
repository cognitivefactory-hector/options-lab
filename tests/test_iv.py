"""Implied-vol solver — the golden invariant is the round-trip:

    price(sigma) -> implied_vol -> recovers sigma within tolerance.

No-solution cases (price below intrinsic, above the no-arbitrage upper bound,
or at/after expiry) must be handled gracefully — we return NaN rather than
raising, so a surface can mask the cell instead of crashing the grid.
"""
import math

import pytest

from lab.pricing.black_scholes import price
from lab.vol.iv import implied_vol

S, K, T, R = 100.0, 100.0, 1.0, 0.05


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("sigma", [0.05, 0.15, 0.2, 0.5, 1.0])
@pytest.mark.parametrize("strike", [80.0, 100.0, 120.0])
def test_round_trip_recovers_input_vol(kind, sigma, strike):
    target = price(S, strike, T, R, sigma, kind)
    recovered = implied_vol(target, S, strike, T, R, kind)
    assert recovered == pytest.approx(sigma, abs=1e-6)


def test_round_trip_with_dividend_yield():
    sigma = 0.25
    target = price(S, K, T, R, sigma, "call", q=0.03)
    assert implied_vol(target, S, K, T, R, "call", q=0.03) == pytest.approx(sigma, abs=1e-6)


def test_higher_price_implies_higher_vol():
    lo = implied_vol(price(S, K, T, R, 0.15, "call"), S, K, T, R, "call")
    hi = implied_vol(price(S, K, T, R, 0.45, "call"), S, K, T, R, "call")
    assert hi > lo


def test_price_below_intrinsic_returns_nan():
    intrinsic = max(S - K * math.exp(-R * T), 0.0)
    assert math.isnan(implied_vol(intrinsic - 1.0, S, K, T, R, "call"))


def test_price_above_upper_bound_returns_nan():
    # A call can never be worth more than the (dividend-discounted) spot.
    assert math.isnan(implied_vol(S + 5.0, S, K, T, R, "call"))


def test_expired_option_returns_nan():
    assert math.isnan(implied_vol(10.0, S, K, 0.0, R, "call"))


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        implied_vol(10.0, S, K, T, R, "banana")
