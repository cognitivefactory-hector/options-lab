"""Implied-volatility solver.

Inverts the Black-Scholes price for sigma. Because BS price is strictly
increasing in vol, the problem is a well-behaved 1-D root find; we use Brent's
method (a bracketed solver — bisection's robustness with faster convergence),
bracketing sigma in (0, SIGMA_MAX].

No-solution cases return NaN rather than raising: a quoted price below
intrinsic or above the no-arbitrage upper bound has no implied vol, and a
surface should mask that cell, not crash. (`kind` validation still raises —
that's a programming error, not market data.)
"""
import math

from scipy.optimize import brentq

from lab.pricing.black_scholes import CALL, PUT, _validate_kind, price

SIGMA_MIN = 1e-9
SIGMA_MAX = 10.0  # 1000% vol — far beyond any real quote.


def _no_arbitrage_bounds(S, K, t, r, kind, q):
    """(lower, upper) price bounds; outside them no implied vol exists."""
    disc_s = S * math.exp(-q * t)
    disc_k = K * math.exp(-r * t)
    if kind == CALL:
        return max(disc_s - disc_k, 0.0), disc_s
    return max(disc_k - disc_s, 0.0), disc_k


def implied_vol(target_price, S, K, t, r, kind, q=0.0):
    """Solve for the volatility that reprices `target_price`.

    Returns NaN when no solution exists (expired option, or a price outside
    the no-arbitrage bounds).
    """
    _validate_kind(kind)
    if t <= 0.0:
        return math.nan

    lower, upper = _no_arbitrage_bounds(S, K, t, r, kind, q)
    # Strictly outside the open band -> no implied vol. A tiny epsilon keeps
    # prices exactly at intrinsic/upper (sigma -> 0 / inf limits) as no-solution.
    if target_price <= lower or target_price >= upper:
        return math.nan

    def objective(sigma):
        return price(S, K, t, r, sigma, kind, q) - target_price

    try:
        return brentq(objective, SIGMA_MIN, SIGMA_MAX, xtol=1e-10, maxiter=200)
    except (ValueError, RuntimeError):
        # No sign change in the bracket / failed convergence.
        return math.nan


# Re-export for callers that want the kind constants alongside the solver.
__all__ = ["CALL", "PUT", "implied_vol"]
