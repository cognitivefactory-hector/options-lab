"""Performance metrics on equity curves and trade-level P&L.

Conventions:
- `max_drawdown` is a positive fraction (0.5 == a 50% peak-to-trough fall).
- `sharpe`/`sortino` are annualized by sqrt(periods_per_year); std uses the
  sample (ddof=1) for Sharpe; Sortino's downside deviation uses 1/N about the
  target return (MAR=0 by default).
- `profit_factor` is +inf when there are no losing trades.
"""
import math
from typing import NamedTuple

import numpy as np


class Metrics(NamedTuple):
    cagr: float
    max_drawdown: float
    sharpe: float
    sortino: float
    win_rate: float
    profit_factor: float


def _returns(equity):
    equity = np.asarray(equity, dtype=float)
    return equity[1:] / equity[:-1] - 1.0


def cagr(equity, periods_per_year=252):
    equity = np.asarray(equity, dtype=float)
    n_periods = len(equity) - 1
    if n_periods <= 0 or equity[0] <= 0:
        return 0.0
    years = n_periods / periods_per_year
    return (equity[-1] / equity[0]) ** (1.0 / years) - 1.0


def max_drawdown(equity):
    equity = np.asarray(equity, dtype=float)
    running_peak = np.maximum.accumulate(equity)
    drawdowns = (equity - running_peak) / running_peak
    return float(-drawdowns.min())


def sharpe(returns, periods_per_year=252, risk_free=0.0):
    returns = np.asarray(returns, dtype=float)
    excess = returns - risk_free / periods_per_year
    sd = excess.std(ddof=1)
    if sd == 0.0:
        return 0.0
    return float(excess.mean() / sd * math.sqrt(periods_per_year))


def sortino(returns, periods_per_year=252, risk_free=0.0, target=0.0):
    returns = np.asarray(returns, dtype=float)
    excess = returns - risk_free / periods_per_year
    downside = np.minimum(returns - target, 0.0)
    downside_dev = math.sqrt(np.mean(downside**2))
    if downside_dev == 0.0:
        return 0.0
    return float(excess.mean() / downside_dev * math.sqrt(periods_per_year))


def win_rate(trade_pnls):
    trade_pnls = np.asarray(trade_pnls, dtype=float)
    if trade_pnls.size == 0:
        return 0.0
    return float((trade_pnls > 0.0).mean())


def profit_factor(trade_pnls):
    trade_pnls = np.asarray(trade_pnls, dtype=float)
    gross_win = trade_pnls[trade_pnls > 0.0].sum()
    gross_loss = -trade_pnls[trade_pnls < 0.0].sum()
    if gross_loss == 0.0:
        return math.inf
    return float(gross_win / gross_loss)


def compute_metrics(equity, trade_pnls=None, periods_per_year=252, risk_free=0.0):
    """Bundle every metric for an equity curve (and optional trade P&L list)."""
    rets = _returns(equity)
    pnls = trade_pnls if trade_pnls is not None else []
    return Metrics(
        cagr=cagr(equity, periods_per_year),
        max_drawdown=max_drawdown(equity),
        sharpe=sharpe(rets, periods_per_year, risk_free),
        sortino=sortino(rets, periods_per_year, risk_free),
        win_rate=win_rate(pnls),
        profit_factor=profit_factor(pnls),
    )
