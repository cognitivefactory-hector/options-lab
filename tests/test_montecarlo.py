"""Monte-Carlo GBM simulation — outcome and drawdown distributions.

The point (per the whiteboard defense) is a *distribution* of outcomes from
many paths, not one lucky history. Determinism under a fixed seed is required
so results are reproducible and testable.
"""
import math

import numpy as np
import pytest

from lab.backtest.montecarlo import drawdown_distribution, simulate_gbm, summarize, terminal_values

S0, MU, SIGMA, T = 100.0, 0.08, 0.2, 1.0


def test_path_shape_and_initial_column():
    paths = simulate_gbm(S0, MU, SIGMA, T, steps=12, n_paths=50, seed=1)
    assert paths.shape == (50, 13)
    np.testing.assert_array_equal(paths[:, 0], np.full(50, S0))


def test_same_seed_is_reproducible():
    a = simulate_gbm(S0, MU, SIGMA, T, steps=12, n_paths=50, seed=42)
    b = simulate_gbm(S0, MU, SIGMA, T, steps=12, n_paths=50, seed=42)
    np.testing.assert_array_equal(a, b)


def test_different_seeds_differ():
    a = simulate_gbm(S0, MU, SIGMA, T, steps=12, n_paths=50, seed=1)
    b = simulate_gbm(S0, MU, SIGMA, T, steps=12, n_paths=50, seed=2)
    assert not np.array_equal(a, b)


def test_zero_vol_is_deterministic_drift():
    paths = simulate_gbm(S0, MU, 0.0, T, steps=12, n_paths=10, seed=1)
    expected_terminal = S0 * math.exp(MU * T)
    np.testing.assert_allclose(terminal_values(paths), np.full(10, expected_terminal))


def test_zero_vol_upward_drift_has_no_drawdown():
    paths = simulate_gbm(S0, MU, 0.0, T, steps=12, n_paths=10, seed=1)
    np.testing.assert_allclose(drawdown_distribution(paths), np.zeros(10), atol=1e-12)


def test_terminal_mean_approaches_lognormal_mean():
    # E[S_T] = S0 * exp(mu * T); with many paths the sample mean is close.
    paths = simulate_gbm(S0, MU, SIGMA, T, steps=50, n_paths=20000, seed=7)
    assert terminal_values(paths).mean() == pytest.approx(S0 * math.exp(MU * T), rel=0.02)


def test_summarize_is_reproducible_and_well_formed():
    paths = simulate_gbm(S0, MU, SIGMA, T, steps=12, n_paths=2000, seed=3)
    s = summarize(paths)
    assert s["p05"] < s["median"] < s["p95"]
    assert summarize(simulate_gbm(S0, MU, SIGMA, T, steps=12, n_paths=2000, seed=3)) == s
