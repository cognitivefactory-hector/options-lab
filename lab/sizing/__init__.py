"""Risk-based position sizing — survive a tail, don't maximize growth."""
from lab.sizing.risk import SizingDecision, fixed_fractional, fractional_kelly, recommend_size

__all__ = ["SizingDecision", "fixed_fractional", "fractional_kelly", "recommend_size"]
