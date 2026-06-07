"""Backtest performance metrics — pure functions on equity curves / P&L lists.

Hand-computed references throughout. These are the numbers a hiring manager
reads, so they must be unambiguous and correct.
"""
import math

import pytest

from lab.backtest.metrics import (
    cagr,
    compute_metrics,
    max_drawdown,
    profit_factor,
    sharpe,
    sortino,
    win_rate,
)


def test_max_drawdown_is_largest_peak_to_trough_fraction():
    # peak 120, trough 60 -> 50% drawdown, returned as a positive fraction.
    assert max_drawdown([100, 120, 60, 90]) == pytest.approx(0.5)


def test_max_drawdown_of_monotonic_curve_is_zero():
    assert max_drawdown([100, 110, 120, 130]) == pytest.approx(0.0)


def test_cagr_doubling_each_period():
    # 100 -> 200 -> 400 over two 1-year periods => 100% CAGR.
    assert cagr([100, 200, 400], periods_per_year=1) == pytest.approx(1.0)


def test_sharpe_zero_mean_returns_is_zero():
    assert sharpe([0.01, -0.01, 0.01, -0.01], periods_per_year=1) == pytest.approx(0.0)


def test_sharpe_known_value():
    # mean 0.01, sample std sqrt(0.0002); ppy=1 -> 0.01/0.0141421 = 0.70711.
    assert sharpe([0.02, 0.00], periods_per_year=1) == pytest.approx(0.70711, abs=1e-5)


def test_sortino_only_penalizes_downside():
    # mean 0.01; downside dev sqrt((-0.01)^2 / 2)=0.0070711; ppy=1 -> 1.41421.
    assert sortino([0.03, -0.01], periods_per_year=1) == pytest.approx(1.41421, abs=1e-5)


def test_win_rate_counts_positive_fraction():
    assert win_rate([1.0, -1.0, 1.0, 1.0]) == pytest.approx(0.75)


def test_profit_factor_gross_win_over_gross_loss():
    assert profit_factor([10.0, -5.0, 5.0]) == pytest.approx(3.0)


def test_profit_factor_is_inf_with_no_losses():
    assert math.isinf(profit_factor([1.0, 2.0, 3.0]))


def test_compute_metrics_bundles_all_fields():
    m = compute_metrics([100, 120, 60, 90], trade_pnls=[20, -60, 30], periods_per_year=1)
    assert m.max_drawdown == pytest.approx(0.5)
    assert m.win_rate == pytest.approx(2 / 3)
    assert hasattr(m, "cagr") and hasattr(m, "sharpe") and hasattr(m, "sortino")
    assert hasattr(m, "profit_factor")
