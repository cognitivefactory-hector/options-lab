"""Backtest engine: reconstructed option P&L, the costs toggle, walk-forward.

Two trust-core invariants are enforced here:
  1. "with costs" net return is *always* below "without costs" on the same data
     (the M4 acceptance gate), at both the single-trade and full-run level.
  2. Walk-forward never lets the fitter see out-of-sample data (no leakage).

Option prices are reconstructed from the underlier + a Black-Scholes vol
assumption — a labeled model approximation, exercised here against BS directly.
"""
import numpy as np
import pytest

from lab.backtest.costs import CostModel
from lab.backtest.engine import LegSpec, reconstruct_option_price, run_backtest, trade_pnl
from lab.backtest.walkforward import run_walk_forward, walk_forward
from lab.pricing.black_scholes import price as bs_price

R, SIGMA = 0.05, 0.2


# --- Reconstruction (labeled BS approximation) --------------------------

def test_reconstruct_matches_black_scholes():
    assert reconstruct_option_price(100, 100, 0.25, R, SIGMA, "call") == pytest.approx(
        bs_price(100, 100, 0.25, R, SIGMA, "call")
    )


def test_reconstruct_at_expiry_is_intrinsic():
    assert reconstruct_option_price(110, 100, 0.0, R, SIGMA, "call") == pytest.approx(10.0)


# --- Single trade P&L (known path) --------------------------------------

def test_long_call_to_expiry_known_pnl():
    # Buy 1 ATM call, hold to expiry, underlier finishes at 110.
    legs = [LegSpec("call", quantity=1, strike=100.0)]
    entry = bs_price(100, 100, 0.25, R, SIGMA, "call")
    pnl = trade_pnl(legs, S_entry=100.0, S_exit=110.0, expiry=0.25, hold=0.25,
                    r=R, sigma=SIGMA, multiplier=100)
    assert pnl == pytest.approx((10.0 - entry) * 100)


def test_costs_strictly_reduce_single_trade_pnl():
    legs = [LegSpec("call", quantity=1, strike=100.0)]
    common = {"S_entry": 100.0, "S_exit": 110.0, "expiry": 0.25, "hold": 0.25,
              "r": R, "sigma": SIGMA}
    gross = trade_pnl(legs, **common, cost_model=None)
    net = trade_pnl(legs, **common, cost_model=CostModel())
    assert net < gross


# --- Full run: the costs toggle invariant (ACCEPTANCE) ------------------

def _price_series():
    # A deterministic zig-zag so trades both win and lose.
    return np.array([100, 104, 99, 107, 95, 110, 102, 108, 101, 106, 100], dtype=float)


def _build_legs(spot):
    # Short an ATM straddle (a short-premium structure that costs matter for).
    return [LegSpec("call", quantity=-1, strike=spot), LegSpec("put", quantity=-1, strike=spot)]


def test_with_costs_never_beats_without_on_same_data():
    prices = _price_series()
    without = run_backtest(prices, _build_legs, hold_periods=2, r=R, sigma=SIGMA, cost_model=None)
    with_costs = run_backtest(prices, _build_legs, hold_periods=2, r=R, sigma=SIGMA,
                              cost_model=CostModel())
    assert with_costs.equity[-1] < without.equity[-1]
    assert with_costs.n_trades == without.n_trades == 5


def test_run_backtest_reports_metrics_and_equity():
    result = run_backtest(_price_series(), _build_legs, hold_periods=2, r=R, sigma=SIGMA)
    assert len(result.equity) == result.n_trades + 1
    assert len(result.trade_pnls) == result.n_trades
    assert hasattr(result.metrics, "max_drawdown")


# --- Walk-forward: splitter + no-leakage --------------------------------

def test_walk_forward_windows_tile_and_dont_leak():
    folds = list(walk_forward(n=10, train=4, test=2, step=2))
    assert len(folds) == 3
    seen_test = []
    for train_idx, test_idx in folds:
        assert max(train_idx) < min(test_idx)          # train strictly precedes test
        assert set(train_idx).isdisjoint(test_idx)     # no overlap within a fold
        seen_test.append(list(test_idx))
    flat = [i for seg in seen_test for i in seg]
    assert len(flat) == len(set(flat))                  # test segments don't overlap


def test_run_walk_forward_never_fits_on_its_own_future():
    # Rolling walk-forward may reuse a *past* fold's test data as later train
    # data; the invariant is per-fold: a fit never sees its OWN fold's future.
    data = np.arange(12)  # values == indices, so a spy can record what it saw
    fitted_per_fold = []

    def fit_fn(train):
        fitted_per_fold.append(set(train.tolist()))
        return train.mean()

    def eval_fn(test, params):
        return test - params  # arbitrary OOS transform

    oos = run_walk_forward(data, fit_fn, eval_fn, train=4, test=2, step=2)
    folds = list(walk_forward(12, 4, 2, 2))
    for fitted, (_, test_idx) in zip(fitted_per_fold, folds, strict=True):
        assert fitted.isdisjoint(test_idx)              # fit never peeked at its OOS window
    test_indices = {i for _, test_idx in folds for i in test_idx}
    assert len(oos) == len(test_indices)                # every OOS point evaluated
