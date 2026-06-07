"""Black-Scholes pricing and analytic Greeks for European options.

Framework-free (no Django imports) and pure: deterministic functions of the
inputs, which is exactly why this layer is built and tested first.

Assumptions (and where they break, per SPEC.md §7): constant volatility, no
early exercise (European — American options with early exercise are out of
scope), and a continuous dividend yield `q`. Document, don't paper over.

Conventions for the raw analytic Greeks (display layers scale as needed):
- `vega` is per 1.0 change in vol (per 100 vol-points), not per 1%.
- `theta` is per year, not per calendar/trading day.
- `rho` is per 1.0 change in the rate, not per 1%.

Parameters used throughout:
    S     spot price of the underlier
    K     strike
    t     time to expiry, in years
    r     continuously-compounded risk-free rate
    sigma volatility (annualized)
    kind  "call" or "put"
    q     continuous dividend yield (default 0.0)
"""
from typing import NamedTuple

import numpy as np
from scipy.stats import norm

CALL = "call"
PUT = "put"


class Greeks(NamedTuple):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


def _validate_kind(kind: str) -> None:
    if kind not in (CALL, PUT):
        raise ValueError(f"kind must be {CALL!r} or {PUT!r}, got {kind!r}")


def _d1_d2(S, K, t, r, sigma, q):
    """d1, d2 from the Black-Scholes formula. Caller guarantees t>0, sigma>0."""
    vol_sqrt_t = sigma * np.sqrt(t)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * t) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return d1, d2


def _intrinsic(S, K, kind):
    return max(S - K, 0.0) if kind == CALL else max(K - S, 0.0)


def price(S, K, t, r, sigma, kind, q=0.0):
    """Black-Scholes price of a European call or put.

    At or past expiry (t<=0), or with zero vol, returns the intrinsic value.
    """
    _validate_kind(kind)
    if t <= 0.0 or sigma <= 0.0:
        return _intrinsic(S, K, kind)
    d1, d2 = _d1_d2(S, K, t, r, sigma, q)
    disc_s = S * np.exp(-q * t)
    disc_k = K * np.exp(-r * t)
    if kind == CALL:
        return disc_s * norm.cdf(d1) - disc_k * norm.cdf(d2)
    return disc_k * norm.cdf(-d2) - disc_s * norm.cdf(-d1)


def delta(S, K, t, r, sigma, kind, q=0.0):
    _validate_kind(kind)
    if t <= 0.0 or sigma <= 0.0:
        # Step function at expiry: 1/0 for a call, -1/0 for a put.
        itm = (S > K) if kind == CALL else (S < K)
        sign = 1.0 if kind == CALL else -1.0
        return sign if itm else 0.0
    d1, _ = _d1_d2(S, K, t, r, sigma, q)
    disc = np.exp(-q * t)
    if kind == CALL:
        return disc * norm.cdf(d1)
    return disc * (norm.cdf(d1) - 1.0)


def gamma(S, K, t, r, sigma, kind=CALL, q=0.0):
    """Identical for calls and puts; `kind` accepted for a uniform signature."""
    _validate_kind(kind)
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    d1, _ = _d1_d2(S, K, t, r, sigma, q)
    return np.exp(-q * t) * norm.pdf(d1) / (S * sigma * np.sqrt(t))


def vega(S, K, t, r, sigma, kind=CALL, q=0.0):
    """Per 1.0 change in vol. Identical for calls and puts."""
    _validate_kind(kind)
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    d1, _ = _d1_d2(S, K, t, r, sigma, q)
    return S * np.exp(-q * t) * norm.pdf(d1) * np.sqrt(t)


def theta(S, K, t, r, sigma, kind, q=0.0):
    """Per year. Negative for long options in the typical case."""
    _validate_kind(kind)
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    d1, d2 = _d1_d2(S, K, t, r, sigma, q)
    disc_s = S * np.exp(-q * t)
    disc_k = K * np.exp(-r * t)
    term1 = -disc_s * norm.pdf(d1) * sigma / (2.0 * np.sqrt(t))
    if kind == CALL:
        return term1 - r * disc_k * norm.cdf(d2) + q * disc_s * norm.cdf(d1)
    return term1 + r * disc_k * norm.cdf(-d2) - q * disc_s * norm.cdf(-d1)


def rho(S, K, t, r, sigma, kind, q=0.0):
    """Per 1.0 change in the rate."""
    _validate_kind(kind)
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    _, d2 = _d1_d2(S, K, t, r, sigma, q)
    disc_k = K * t * np.exp(-r * t)
    if kind == CALL:
        return disc_k * norm.cdf(d2)
    return -disc_k * norm.cdf(-d2)


def greeks(S, K, t, r, sigma, kind, q=0.0):
    """All five Greeks in one pass, returned as a `Greeks` namedtuple."""
    return Greeks(
        delta=delta(S, K, t, r, sigma, kind, q),
        gamma=gamma(S, K, t, r, sigma, kind, q),
        theta=theta(S, K, t, r, sigma, kind, q),
        vega=vega(S, K, t, r, sigma, kind, q),
        rho=rho(S, K, t, r, sigma, kind, q),
    )
