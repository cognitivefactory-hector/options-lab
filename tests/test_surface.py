"""IV surface — a strike x expiry grid that exposes skew and term structure.

Built by inverting option prices to implied vols cell by cell, so the core
test is again a round-trip: prices generated from a known vol grid must invert
back to that grid. `skew` is a fixed-expiry slice across strikes; term
structure is a fixed-strike slice across expiries.
"""
import numpy as np

from lab.pricing.black_scholes import price
from lab.vol.surface import build_surface

SPOT, R = 100.0, 0.05
STRIKES = np.array([80.0, 90.0, 100.0, 110.0, 120.0])
EXPIRIES = np.array([0.25, 0.5, 1.0])

# A volatility smile (high at the wings) that steepens at short tenors.
VOL_GRID = np.array(
    [
        [0.32, 0.26, 0.22, 0.27, 0.34],  # 0.25y
        [0.30, 0.25, 0.22, 0.26, 0.31],  # 0.5y
        [0.28, 0.24, 0.22, 0.25, 0.29],  # 1.0y
    ]
)


def _price_grid(kind="call"):
    grid = np.empty_like(VOL_GRID)
    for i, t in enumerate(EXPIRIES):
        for j, k in enumerate(STRIKES):
            grid[i, j] = price(SPOT, k, t, R, VOL_GRID[i, j], kind)
    return grid


def test_surface_inverts_prices_back_to_vol_grid():
    surface = build_surface(_price_grid(), STRIKES, EXPIRIES, SPOT, R, kind="call")
    np.testing.assert_allclose(surface.iv, VOL_GRID, atol=1e-6)


def test_surface_shape_and_axes():
    surface = build_surface(_price_grid(), STRIKES, EXPIRIES, SPOT, R, kind="call")
    assert surface.iv.shape == (len(EXPIRIES), len(STRIKES))
    np.testing.assert_array_equal(surface.strikes, STRIKES)
    np.testing.assert_array_equal(surface.expiries, EXPIRIES)


def test_skew_returns_strike_slice_at_expiry():
    surface = build_surface(_price_grid(), STRIKES, EXPIRIES, SPOT, R, kind="call")
    strikes, ivs = surface.skew(0.5)
    np.testing.assert_array_equal(strikes, STRIKES)
    np.testing.assert_allclose(ivs, VOL_GRID[1], atol=1e-6)
    # Smile: the wings sit above the ATM strike.
    atm = np.argmin(np.abs(STRIKES - SPOT))
    assert ivs[0] > ivs[atm] and ivs[-1] > ivs[atm]


def test_term_structure_returns_expiry_slice_at_strike():
    surface = build_surface(_price_grid(), STRIKES, EXPIRIES, SPOT, R, kind="call")
    expiries, ivs = surface.term_structure(100.0)
    np.testing.assert_array_equal(expiries, EXPIRIES)
    np.testing.assert_allclose(ivs, VOL_GRID[:, 2], atol=1e-6)


def test_skew_and_term_structure_snap_to_nearest_axis_value():
    surface = build_surface(_price_grid(), STRIKES, EXPIRIES, SPOT, R, kind="call")
    # 0.48 snaps to the 0.5y row; 102 snaps to the 100 strike column.
    _, skew_ivs = surface.skew(0.48)
    np.testing.assert_allclose(skew_ivs, VOL_GRID[1], atol=1e-6)
    _, ts_ivs = surface.term_structure(102.0)
    np.testing.assert_allclose(ts_ivs, VOL_GRID[:, 2], atol=1e-6)
