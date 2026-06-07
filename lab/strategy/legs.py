"""Multi-leg strategy engine — payoff, breakevens, extrema, net Greeks.

Framework-free. A position is a list of `Leg`s; each leg is an option
(call/put) or the underlier (stock). Everything is computed on a per-share
basis (a leg's `multiplier` defaults to 1) so reference cases stay hand-
computable; real option contracts use multiplier=100.

Conventions:
- `quantity` is signed: +long, -short.
- `premium` is the per-share entry price (option premium, or stock entry).
- P&L is net of entry: payoff(S_T) = sum_legs qty*mult*(value(S_T) - premium).
- `entry_cost` is a net debit when positive, a net credit when negative.

At-expiry methods (payoff/breakevens/max_profit/max_loss) assume every leg
shares one expiry. Multi-expiry structures (calendars) raise from those
methods and must be read through `mark_to_model`, which respects each leg's
own time to expiry.
"""
import math
from dataclasses import dataclass

import numpy as np

from lab.pricing import Greeks
from lab.pricing import black_scholes as bs

CALL, PUT, STOCK = "call", "put", "stock"
_KINDS = (CALL, PUT, STOCK)


@dataclass
class Leg:
    kind: str
    quantity: float
    strike: float | None = None
    premium: float = 0.0
    expiry: float | None = None
    multiplier: float = 1.0

    def __post_init__(self):
        if self.kind not in _KINDS:
            raise ValueError(f"kind must be one of {_KINDS}, got {self.kind!r}")

    def intrinsic(self, S_T):
        """Per-share value at terminal spot S_T (ignores entry premium)."""
        if self.kind == CALL:
            return np.maximum(S_T - self.strike, 0.0)
        if self.kind == PUT:
            return np.maximum(self.strike - S_T, 0.0)
        if self.kind == STOCK:
            return S_T
        raise ValueError(f"unknown kind {self.kind!r}")

    def payoff(self, S_T):
        """Per-leg net P&L at expiry, including sign, size and entry cost."""
        return self.quantity * self.multiplier * (self.intrinsic(S_T) - self.premium)


class Strategy:
    def __init__(self, legs: list[Leg]):
        self.legs = list(legs)

    # --- helpers ---------------------------------------------------------

    def _option_legs(self):
        return [leg for leg in self.legs if leg.kind in (CALL, PUT)]

    def _require_single_expiry(self):
        expiries = {leg.expiry for leg in self._option_legs() if leg.expiry is not None}
        if len(expiries) > 1:
            raise ValueError(
                "at-expiry methods require a single common expiry; this position "
                "spans multiple expiries — use mark_to_model() instead"
            )

    def _strikes(self):
        return sorted({leg.strike for leg in self._option_legs()})

    def _payoff_nodes(self):
        """Spot nodes spanning the piecewise-linear payoff: 0, strikes, upper.

        Between consecutive nodes the payoff is exactly linear (kinks only at
        strikes), so zero-crossings interpolate exactly.
        """
        strikes = self._strikes()
        refs = strikes + [leg.premium for leg in self.legs if leg.kind == STOCK]
        hi = (max(refs) if refs else 100.0) * 5.0 + 100.0
        return sorted({0.0, *strikes, hi})

    def _right_slope(self):
        """Payoff slope as S_T -> +inf (sign tells us if a wing is unbounded)."""
        a = self._payoff_nodes()[-1]
        b = a + 1.0
        return float((self.payoff(b) - self.payoff(a)) / (b - a))

    # --- at-expiry analytics --------------------------------------------

    def payoff(self, S_T):
        self._require_single_expiry()
        total = sum(leg.payoff(S_T) for leg in self.legs)
        return total if isinstance(S_T, np.ndarray) else float(total)

    def entry_cost(self):
        """Net debit (>0) or credit (<0) to open the position."""
        return float(sum(leg.quantity * leg.multiplier * leg.premium for leg in self.legs))

    def breakevens(self):
        self._require_single_expiry()
        nodes = self._payoff_nodes()
        fvals = [self.payoff(x) for x in nodes]
        crossings = []
        points = list(zip(nodes, fvals, strict=True))
        for (a, fa), (b, fb) in zip(points, points[1:], strict=False):
            if abs(fa) < 1e-12:
                crossings.append(a)
            if (fa < 0.0 < fb) or (fa > 0.0 > fb):
                crossings.append(a - fa * (b - a) / (fb - fa))
        if abs(fvals[-1]) < 1e-12:
            crossings.append(nodes[-1])
        # Dedupe within tolerance.
        out = []
        for x in sorted(crossings):
            if not out or abs(x - out[-1]) > 1e-9:
                out.append(x)
        return out

    def max_profit(self):
        self._require_single_expiry()
        if self._right_slope() > 1e-12:
            return math.inf
        return max(self.payoff(x) for x in self._payoff_nodes())

    def max_loss(self):
        self._require_single_expiry()
        if self._right_slope() < -1e-12:
            return -math.inf
        return min(self.payoff(x) for x in self._payoff_nodes())

    # --- model-based analytics (respect each leg's own expiry) -----------

    def net_greeks(self, S, r, sigma, q=0.0):
        total = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}
        for leg in self.legs:
            scale = leg.quantity * leg.multiplier
            if leg.kind == STOCK:
                total["delta"] += scale  # dV/dS = 1 per share; other Greeks zero.
                continue
            g = bs.greeks(S, leg.strike, leg.expiry, r, sigma, leg.kind, q)
            for name in total:
                total[name] += scale * getattr(g, name)
        return Greeks(**total)

    def mark_to_model(self, S, r, sigma, q=0.0):
        """Net P&L now, valuing each leg with Black-Scholes at its own expiry."""
        total = 0.0
        for leg in self.legs:
            scale = leg.quantity * leg.multiplier
            if leg.kind == STOCK:
                total += scale * (S - leg.premium)
            else:
                value = bs.price(S, leg.strike, leg.expiry, r, sigma, leg.kind, q)
                total += scale * (value - leg.premium)
        return float(total)

    def prob_profit(self, S, r, sigma, t, q=0.0, drift=None):
        """P(payoff(S_T) > 0) under a lognormal terminal distribution.

        Drift defaults to the risk-neutral (r - q). Integrates the lognormal
        density over the spot regions where the at-expiry payoff is positive.
        """
        self._require_single_expiry()
        if drift is None:
            drift = r - q
        mu = math.log(S) + (drift - 0.5 * sigma**2) * t
        sd = sigma * math.sqrt(t)

        def ln_cdf(x):
            if x <= 0.0:
                return 0.0
            return float(bs.norm.cdf((math.log(x) - mu) / sd))

        # Boundaries of constant-sign regions: 0, breakevens, +inf.
        bounds = [0.0, *self.breakevens(), math.inf]
        p = 0.0
        for a, b in zip(bounds, bounds[1:], strict=False):
            mid = (a + 1.0) if math.isinf(b) else 0.5 * (a + b)
            if self.payoff(mid) > 0.0:
                upper = 1.0 if math.isinf(b) else ln_cdf(b)
                p += upper - ln_cdf(a)
        return p
