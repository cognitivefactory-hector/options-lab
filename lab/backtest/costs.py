"""Explicit trading-cost model: commission, bid/ask spread, slippage, assignment.

Retail backtests that ignore these die live. The whole point is to *see* the
edge shrink once friction is in — so the UI exposes a with/without-costs
toggle, and the engine guarantees costs are always non-negative (strictly
positive whenever a position trades), which is what makes "with costs can
never beat without costs" hold by construction.

Defaults are deliberately modest, defensible retail numbers (record the
rationale in DECISIONS.md): ~$0.65/contract commission, a 1c half-spread, and
a couple of bps of slippage on notional.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    commission_per_contract: float = 0.65
    half_spread_per_share: float = 0.01
    slippage_bps: float = 2.0
    assignment_fee: float = 5.0
    multiplier: int = 100

    def round_trip_cost(self, *, contracts, entry_price, exit_price, assigned=False):
        """Total friction to open *and* close `contracts` contracts.

        Commission is charged per contract per side; the bid/ask spread is
        crossed on each side; slippage is a few bps of the traded notional.
        """
        n = abs(contracts)
        if n == 0:
            return 0.0
        shares = n * self.multiplier
        commission = self.commission_per_contract * n * 2  # entry + exit
        spread = self.half_spread_per_share * shares * 2     # crossed each side
        slippage = (self.slippage_bps / 1e4) * (entry_price + exit_price) * shares
        assignment = self.assignment_fee if assigned else 0.0
        return commission + spread + slippage + assignment
