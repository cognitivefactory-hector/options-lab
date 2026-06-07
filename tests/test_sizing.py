"""Risk-based position sizing — built to survive a tail, not maximize growth.

Two invariants matter (PLAN.md M5): fixed-fractional never risks more than the
allotted fraction of capital, and Kelly is always capped/fractional — never
full Kelly (which blows up on a fat tail). A negative edge sizes to zero: the
sizing layer can also say "don't trade".
"""
import pytest

from lab.sizing.risk import SizingDecision, fixed_fractional, fractional_kelly, recommend_size

# --- fixed fractional ----------------------------------------------------

def test_fixed_fractional_contract_count():
    # Risk 2% of 100k = $2,000; each contract can lose $500 -> 4 contracts.
    assert fixed_fractional(capital=100_000, risk_fraction=0.02, risk_per_contract=500) == 4


def test_fixed_fractional_never_exceeds_the_risk_budget():
    contracts = fixed_fractional(capital=100_000, risk_fraction=0.02, risk_per_contract=700)
    assert contracts * 700 <= 0.02 * 100_000  # floored, never over budget


def test_fixed_fractional_can_be_zero_when_one_unit_is_too_risky():
    assert fixed_fractional(capital=10_000, risk_fraction=0.01, risk_per_contract=500) == 0


# --- fractional / capped Kelly ------------------------------------------

def test_half_kelly_known_value():
    # p=0.6, win:loss = 1:1 -> f* = (0.6*1 - 0.4)/1 = 0.2; half-Kelly = 0.10.
    assert fractional_kelly(win_prob=0.6, win_loss_ratio=1.0) == pytest.approx(0.10)


def test_kelly_is_capped_and_never_full():
    # Big edge: f* = (0.9*2 - 0.1)/2 = 0.85. Result must stay <= cap and < full.
    full = 0.85
    f = fractional_kelly(win_prob=0.9, win_loss_ratio=2.0, kelly_fraction=1.0, cap=0.5)
    assert f == pytest.approx(0.5)
    assert f < full


def test_default_fractional_kelly_is_below_full_for_any_positive_edge():
    full = (0.7 * 1.5 - 0.3) / 1.5
    f = fractional_kelly(win_prob=0.7, win_loss_ratio=1.5)  # default half-Kelly
    assert 0.0 < f < full


def test_negative_edge_sizes_to_zero():
    assert fractional_kelly(win_prob=0.4, win_loss_ratio=1.0) == 0.0


# --- recommendation surfaces the rationale ------------------------------

def test_recommend_size_returns_decision_with_rationale():
    d = recommend_size(capital=100_000, risk_fraction=0.02, risk_per_contract=500)
    assert isinstance(d, SizingDecision)
    assert d.contracts == 4
    assert d.capital_at_risk == pytest.approx(2_000)
    assert d.capital_at_risk <= 0.02 * 100_000
    assert isinstance(d.rationale, str) and d.rationale
