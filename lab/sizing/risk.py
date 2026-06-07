"""Risk-based position sizing.

The conscious trade (DECISIONS.md): size to **survive a fat tail**, not to
maximize growth. Two methods:

- **fixed-fractional** — risk at most a fixed fraction of capital per trade,
  given a defined worst-case loss per contract. Floors to whole contracts, so
  it can legitimately return 0 ("one unit is too much risk → don't trade").
- **capped/fractional Kelly** — Kelly points at the growth-maximizing bet, but
  full Kelly blows up on a fat tail. We always take a *fraction* of Kelly and
  *cap* it, so the result is never full Kelly; a non-positive edge sizes to 0.
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SizingDecision:
    contracts: int
    capital_at_risk: float
    fraction_of_capital: float
    method: str
    rationale: str


def fixed_fractional(capital, risk_fraction, risk_per_contract):
    """Whole contracts whose total worst-case loss stays within the budget.

    Budget = risk_fraction * capital; contracts = floor(budget / per-contract
    risk). Returns 0 when a single contract already exceeds the budget.
    """
    if risk_per_contract <= 0:
        raise ValueError("risk_per_contract must be positive")
    budget = risk_fraction * capital
    return int(math.floor(budget / risk_per_contract))


def fractional_kelly(win_prob, win_loss_ratio, kelly_fraction=0.5, cap=0.5):
    """Capped, fractional Kelly bet size as a fraction of capital.

    f* = (p*b - q) / b, with b = win_loss_ratio, q = 1 - p. We return
    clamp(kelly_fraction * f*, 0, cap): never negative (no edge → 0), never
    above the cap, and with the default half-Kelly, never full.
    """
    p = win_prob
    b = win_loss_ratio
    if b <= 0:
        raise ValueError("win_loss_ratio must be positive")
    f_star = (p * b - (1.0 - p)) / b
    if f_star <= 0.0:
        return 0.0
    return min(kelly_fraction * f_star, cap)


def recommend_size(capital, risk_fraction, risk_per_contract, method="fixed_fractional"):
    """A sizing decision that surfaces the tail-survival rationale."""
    contracts = fixed_fractional(capital, risk_fraction, risk_per_contract)
    capital_at_risk = contracts * risk_per_contract
    rationale = (
        f"Fixed-fractional: risk at most {risk_fraction:.1%} of capital "
        f"(${risk_fraction * capital:,.0f}) per trade. Sized to survive the "
        f"defined worst case (${risk_per_contract:,.0f}/contract), not to "
        f"maximize growth — {contracts} contract(s), "
        f"${capital_at_risk:,.0f} at risk."
    )
    return SizingDecision(
        contracts=contracts,
        capital_at_risk=capital_at_risk,
        fraction_of_capital=capital_at_risk / capital if capital else 0.0,
        method=method,
        rationale=rationale,
    )
