"""Monte-Carlo simulation of underlier paths via geometric Brownian motion.

Produces an *outcome distribution* (and a drawdown distribution) from many
paths rather than one history — the honest way to talk about what a strategy
might do. All randomness flows through a seeded NumPy Generator so runs are
reproducible.
"""
import numpy as np

from lab.backtest.metrics import max_drawdown


def simulate_gbm(S0, mu, sigma, t, steps, n_paths, seed):
    """Simulate `n_paths` GBM paths over `t` years in `steps` increments.

    Returns an array of shape (n_paths, steps+1); column 0 is S0.
    """
    rng = np.random.default_rng(seed)
    dt = t / steps
    z = rng.standard_normal((n_paths, steps))
    increments = np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
    paths = np.empty((n_paths, steps + 1))
    paths[:, 0] = S0
    paths[:, 1:] = S0 * np.cumprod(increments, axis=1)
    return paths


def terminal_values(paths):
    """Terminal price of each path."""
    return paths[:, -1]


def drawdown_distribution(paths):
    """Max drawdown (positive fraction) of each path."""
    return np.array([max_drawdown(path) for path in paths])


def summarize(paths):
    """Distribution summary of terminal values and per-path drawdowns."""
    terminal = terminal_values(paths)
    dd = drawdown_distribution(paths)
    return {
        "mean": float(terminal.mean()),
        "median": float(np.median(terminal)),
        "std": float(terminal.std(ddof=1)),
        "p05": float(np.percentile(terminal, 5)),
        "p95": float(np.percentile(terminal, 95)),
        "prob_loss": float((terminal < paths[0, 0]).mean()),
        "mean_drawdown": float(dd.mean()),
        "max_drawdown": float(dd.max()),
    }
