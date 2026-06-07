"""Studio orchestration — ties the quant modules together for the UI.

Framework-free (no Django): the Django views call these functions and render
the results. Premiums for builder positions are derived from Black-Scholes so
payoff, Greeks and P(profit) are internally consistent without asking the user
to hand-enter eight option prices.
"""
import numpy as np

from lab.backtest.costs import CostModel
from lab.backtest.engine import LegSpec, run_backtest
from lab.backtest.montecarlo import simulate_gbm
from lab.pricing import black_scholes as bs
from lab.regime.vol_regime import classify
from lab.strategy import legs as legmod
from lab.strategy import presets
from lab.vol.surface import build_surface

# Builder presets and how their strikes are placed around spot (fraction of spot).
PRESETS = {
    "iron_condor": "Iron condor",
    "vertical_spread": "Bull call spread",
    "straddle": "Straddle",
    "strangle": "Strangle",
    "covered_call": "Covered call",
}


def _rnd(x):
    return round(x, 2)


def build_position(preset, spot, sigma, r, dte_years, qty=1):
    """Construct a preset position with BS-consistent premiums around `spot`."""
    t = dte_years

    def prem(K, kind):
        return _rnd(bs.price(spot, K, t, r, sigma, kind))

    if preset == "covered_call":
        k = _rnd(spot * 1.05)
        return presets.covered_call(spot, k, prem(k, "call"), expiry=t, qty=qty)
    if preset == "vertical_spread":
        lo, hi = _rnd(spot), _rnd(spot * 1.05)
        return presets.vertical_spread("call", lo, hi, prem(lo, "call"), prem(hi, "call"),
                                       expiry=t, qty=qty)
    if preset == "straddle":
        k = _rnd(spot)
        return presets.straddle(k, prem(k, "call"), prem(k, "put"), expiry=t, qty=qty)
    if preset == "strangle":
        kc, kp = _rnd(spot * 1.05), _rnd(spot * 0.95)
        return presets.strangle(kc, kp, prem(kc, "call"), prem(kp, "put"), expiry=t, qty=qty)
    if preset == "iron_condor":
        lp, sp = _rnd(spot * 0.90), _rnd(spot * 0.95)
        sc, lc = _rnd(spot * 1.05), _rnd(spot * 1.10)
        return presets.iron_condor(lp, sp, sc, lc,
                                   prem(lp, "put"), prem(sp, "put"),
                                   prem(sc, "call"), prem(lc, "call"), expiry=t, qty=qty)
    raise ValueError(f"unknown preset {preset!r}")


def _finite(x):
    """Map +/-inf to None so templates can show an unbounded marker."""
    return None if not np.isfinite(x) else _rnd(x)


def position_summary(strategy, spot, sigma, r, dte_years):
    g = strategy.net_greeks(spot, r, sigma)
    return {
        "breakevens": [_rnd(b) for b in strategy.breakevens()],
        "max_profit": _finite(strategy.max_profit()),
        "max_loss": _finite(strategy.max_loss()),
        "entry_cost": _rnd(strategy.entry_cost()),
        "prob_profit": round(strategy.prob_profit(spot, r, sigma, dte_years), 4),
        "greeks": {k: round(v, 4) for k, v in g._asdict().items()},
        "legs": [
            {"kind": leg.kind, "quantity": leg.quantity,
             "strike": leg.strike, "premium": _rnd(leg.premium)}
            for leg in strategy.legs
        ],
    }


def payoff_series(strategy, spot, lo_frac=0.6, hi_frac=1.4, n=240):
    spots = np.linspace(spot * lo_frac, spot * hi_frac, n)
    return spots, strategy.payoff(spots)


def regime_for(closes):
    """Verdict + read for an underlier close series."""
    verdict, read = classify(closes)
    return verdict, read


def stress_closes(base):
    """Append an illustrative recent vol blow-up so the filter shows SIT_OUT.

    Lets the demo surface the headline judgment output — the regime where the
    tool says "sit out" — on top of any live series.
    """
    base = np.asarray(base, dtype=float)
    shock = np.empty(25)
    shock[0::2] = 0.06
    shock[1::2] = -0.06
    spike = base[-1] * np.exp(np.cumsum(shock))
    return np.concatenate([base, spike])


def scenario_closes(name, base):
    """Resolve a regime scenario name to a close series."""
    return stress_closes(base) if name == "spike" else np.asarray(base, dtype=float)


def illustrative_surface(spot, r, expiries=(0.08, 0.25, 0.5, 1.0)):
    """An illustrative IV surface: impose a smile/term shape, price, re-invert.

    Demonstrates the surface/skew/term-structure tools. Labeled illustrative in
    the UI — it is a constructed shape, not real chain data (SPEC.md §5).
    """
    strikes = np.round(np.linspace(spot * 0.80, spot * 1.20, 9), 2)
    expiries = np.array(expiries)
    prices = np.empty((expiries.size, strikes.size))
    for i, t in enumerate(expiries):
        for j, k in enumerate(strikes):
            moneyness = (k - spot) / spot
            # Smile (convex in moneyness) that flattens with tenor.
            vol = 0.18 + 0.45 * moneyness**2 / np.sqrt(t) - 0.04 * moneyness
            prices[i, j] = bs.price(spot, k, t, r, max(vol, 0.05), "call")
    return build_surface(prices, strikes, expiries, spot, r, kind="call")


def short_straddle_legs(spot):
    """Sell an ATM straddle — the demo's short-premium backtest structure."""
    k = round(spot, 2)
    return [LegSpec("call", -1, k), LegSpec("put", -1, k)]


def backtest_demo(closes, sigma, r=0.04, hold_periods=21):
    """Run the demo strategy with and without costs over a close series."""
    common = dict(hold_periods=hold_periods, r=r, sigma=sigma)
    without = run_backtest(closes, short_straddle_legs, cost_model=None, **common)
    with_costs = run_backtest(closes, short_straddle_legs, cost_model=CostModel(), **common)
    return without, with_costs


def montecarlo_demo(spot, mu, sigma, t=1.0, steps=126, n_paths=400, seed=7):
    return simulate_gbm(spot, mu, sigma, t, steps, n_paths, seed)


# Convenience re-exports the views lean on.
Strategy = legmod.Strategy
