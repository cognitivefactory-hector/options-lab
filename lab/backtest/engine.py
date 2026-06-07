"""Backtest engine: reconstructed option P&L and a costs-toggled run.

Where real historical option chains aren't available, option prices are
**reconstructed from the underlier path + a Black-Scholes vol assumption**.
This is a deliberate, disclosed model approximation (SPEC.md §5 / DECISIONS.md):
it proves method, not a live edge. Every reconstructed price flows through
`reconstruct_option_price` so the assumption has exactly one home.
"""
from typing import NamedTuple

import numpy as np

from lab.backtest.costs import CostModel
from lab.backtest.metrics import Metrics, compute_metrics
from lab.pricing import black_scholes as bs


class LegSpec(NamedTuple):
    kind: str          # "call" or "put"
    quantity: float    # signed: +long / -short
    strike: float


class BacktestResult(NamedTuple):
    equity: np.ndarray
    trade_pnls: list
    metrics: Metrics
    n_trades: int


def reconstruct_option_price(S, K, t, r, sigma, kind, q=0.0):
    """Model price of an option from the underlier + a BS vol assumption.

    A labeled approximation, not a real quote. At/after expiry it is intrinsic.
    """
    return bs.price(S, K, t, r, sigma, kind, q)


def trade_pnl(legs, S_entry, S_exit, *, expiry, hold, r, sigma, q=0.0,
              cost_model: CostModel | None = None, multiplier=100):
    """Net P&L of opening `legs` at S_entry and closing after `hold` years.

    Entry is priced at time-to-expiry `expiry`; exit at `expiry - hold` (zero or
    below settles at intrinsic). With a `cost_model`, round-trip friction is
    subtracted per leg, so the result is always <= the frictionless P&L.
    """
    exit_ttm = max(expiry - hold, 0.0)
    gross = 0.0
    cost = 0.0
    for leg in legs:
        entry_price = reconstruct_option_price(S_entry, leg.strike, expiry, r, sigma, leg.kind, q)
        exit_price = reconstruct_option_price(S_exit, leg.strike, exit_ttm, r, sigma, leg.kind, q)
        gross += leg.quantity * (exit_price - entry_price) * multiplier
        if cost_model is not None:
            assigned = exit_ttm <= 0.0 and leg.quantity < 0 and exit_price > 0.0
            cost += cost_model.round_trip_cost(
                contracts=leg.quantity, entry_price=entry_price,
                exit_price=exit_price, assigned=assigned,
            )
    return gross - cost


def run_backtest(prices, build_legs, *, hold_periods, r, sigma, q=0.0,
                 cost_model: CostModel | None = None, multiplier=100,
                 periods_per_year=252, starting_capital=100_000.0):
    """Roll a strategy over `prices` in non-overlapping holds; report equity.

    At each rebalance the position from `build_legs(spot)` is opened, priced via
    reconstruction, held `hold_periods` bars (one option life), then settled.
    Pass `cost_model=None` for the frictionless leg of the with/without toggle.
    """
    prices = np.asarray(prices, dtype=float)
    expiry = hold_periods / periods_per_year
    hold = expiry  # the option expires exactly at the close of the hold.

    trade_pnls = []
    i = 0
    while i + hold_periods < len(prices):
        legs = build_legs(prices[i])
        pnl = trade_pnl(legs, prices[i], prices[i + hold_periods], expiry=expiry, hold=hold,
                        r=r, sigma=sigma, q=q, cost_model=cost_model, multiplier=multiplier)
        trade_pnls.append(pnl)
        i += hold_periods

    equity = starting_capital + np.concatenate([[0.0], np.cumsum(trade_pnls)])
    trades_per_year = periods_per_year / hold_periods
    metrics = compute_metrics(equity, trade_pnls, periods_per_year=trades_per_year)
    return BacktestResult(equity=equity, trade_pnls=trade_pnls, metrics=metrics,
                          n_trades=len(trade_pnls))
