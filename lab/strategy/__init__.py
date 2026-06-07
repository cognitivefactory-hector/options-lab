"""Strategy builder — multi-leg payoff, breakevens, extrema, net Greeks, presets."""
from lab.strategy.legs import Leg, Strategy
from lab.strategy.presets import (
    calendar,
    covered_call,
    iron_condor,
    straddle,
    strangle,
    vertical_spread,
)

__all__ = [
    "Leg",
    "Strategy",
    "calendar",
    "covered_call",
    "iron_condor",
    "straddle",
    "strangle",
    "vertical_spread",
]
