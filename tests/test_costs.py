"""Cost model — commission, bid/ask spread, slippage, assignment.

The trust-core invariant lives here: trading costs are always non-negative,
and strictly positive whenever a position actually trades. The backtest relies
on that so "with costs" can never beat "without costs".
"""
import pytest

from lab.backtest.costs import CostModel


def test_zero_contracts_costs_nothing():
    assert CostModel().round_trip_cost(contracts=0, entry_price=5.0, exit_price=6.0) == 0.0


def test_any_trade_costs_something_positive():
    cost = CostModel().round_trip_cost(contracts=1, entry_price=5.0, exit_price=6.0)
    assert cost > 0.0


def test_cost_scales_with_contracts():
    m = CostModel()
    one = m.round_trip_cost(contracts=1, entry_price=5.0, exit_price=6.0)
    ten = m.round_trip_cost(contracts=10, entry_price=5.0, exit_price=6.0)
    assert ten == pytest.approx(10 * one)


def test_assignment_adds_a_fee():
    m = CostModel(assignment_fee=5.0)
    base = m.round_trip_cost(contracts=1, entry_price=5.0, exit_price=6.0, assigned=False)
    assigned = m.round_trip_cost(contracts=1, entry_price=5.0, exit_price=6.0, assigned=True)
    assert assigned == pytest.approx(base + 5.0)


def test_wider_spread_costs_more():
    cheap = CostModel(half_spread_per_share=0.01)
    dear = CostModel(half_spread_per_share=0.05)
    assert dear.round_trip_cost(contracts=1, entry_price=5.0, exit_price=6.0) > (
        cheap.round_trip_cost(contracts=1, entry_price=5.0, exit_price=6.0)
    )


def test_zero_cost_model_is_frictionless():
    free = CostModel(commission_per_contract=0.0, half_spread_per_share=0.0,
                     slippage_bps=0.0, assignment_fee=0.0)
    assert free.round_trip_cost(contracts=10, entry_price=5.0, exit_price=6.0) == 0.0
