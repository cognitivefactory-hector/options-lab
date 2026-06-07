"""Implied-volatility surface: a strike x expiry grid of implied vols.

Built by inverting an option-price grid cell by cell. Two read-outs matter for
the judgment story: **skew** (how IV varies across strikes at a fixed expiry —
the smile/smirk) and **term structure** (how IV varies across expiries at a
fixed strike). Cells with no valid implied vol come through as NaN.

Per SPEC.md §5, where real chains aren't available the price grid is itself a
Black-Scholes reconstruction — label such surfaces as illustrative upstream.
"""
from dataclasses import dataclass

import numpy as np

from lab.vol.iv import implied_vol


@dataclass(frozen=True)
class IVSurface:
    strikes: np.ndarray   # 1-D, ascending
    expiries: np.ndarray  # 1-D (years), ascending
    iv: np.ndarray        # 2-D [expiry, strike]
    spot: float

    def _nearest(self, axis: np.ndarray, value: float) -> int:
        return int(np.argmin(np.abs(axis - value)))

    def skew(self, expiry: float):
        """IV across strikes at the expiry nearest `expiry`."""
        row = self._nearest(self.expiries, expiry)
        return self.strikes, self.iv[row]

    def term_structure(self, strike: float):
        """IV across expiries at the strike nearest `strike` (ATM by default)."""
        col = self._nearest(self.strikes, strike)
        return self.expiries, self.iv[:, col]


def build_surface(prices, strikes, expiries, spot, r, kind="call", q=0.0):
    """Invert a 2-D price grid [expiry, strike] into an `IVSurface`."""
    prices = np.asarray(prices, dtype=float)
    strikes = np.asarray(strikes, dtype=float)
    expiries = np.asarray(expiries, dtype=float)

    if prices.shape != (expiries.size, strikes.size):
        raise ValueError(
            f"prices shape {prices.shape} != (expiries, strikes) "
            f"({expiries.size}, {strikes.size})"
        )

    iv = np.empty_like(prices)
    for i, t in enumerate(expiries):
        for j, k in enumerate(strikes):
            iv[i, j] = implied_vol(prices[i, j], spot, k, t, r, kind, q)

    return IVSurface(strikes=strikes, expiries=expiries, iv=iv, spot=float(spot))
