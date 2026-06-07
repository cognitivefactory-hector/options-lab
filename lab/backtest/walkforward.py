"""Walk-forward (out-of-sample) evaluation.

The discipline that earns trust: parameters are fit on a rolling in-sample
window and only ever evaluated on the *next, disjoint* out-of-sample window —
never a single in-sample fit, never a peek at the future. `walk_forward` yields
the (train, test) index windows; `run_walk_forward` drives a fit/eval pair over
them and concatenates the OOS results.
"""
import numpy as np


def walk_forward(n, train, test, step=None):
    """Yield (train_indices, test_indices) ranges tiling a series of length n.

    Each test window immediately follows its train window and never overlaps
    it. `step` (default = `test`) controls how far the origin advances, so the
    default tiles the out-of-sample region without gaps or overlap.
    """
    if train <= 0 or test <= 0:
        raise ValueError("train and test must be positive")
    step = step or test
    start = 0
    while start + train + test <= n:
        train_idx = range(start, start + train)
        test_idx = range(start + train, start + train + test)
        yield train_idx, test_idx
        start += step


def run_walk_forward(data, fit_fn, eval_fn, train, test, step=None):
    """Fit on each in-sample window, evaluate on the next out-of-sample window.

    `fit_fn(train_slice) -> params`; `eval_fn(test_slice, params) -> array`.
    Returns the concatenated OOS evaluations, in time order.
    """
    data = np.asarray(data)
    out = []
    for train_idx, test_idx in walk_forward(len(data), train, test, step):
        params = fit_fn(data[list(train_idx)])
        out.append(np.asarray(eval_fn(data[list(test_idx)], params)))
    return np.concatenate(out) if out else np.array([])
