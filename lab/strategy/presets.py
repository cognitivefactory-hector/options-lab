"""Common option-strategy presets, built on the `Leg`/`Strategy` engine.

Each returns a `Strategy`. Premiums are per-share entry prices; `qty` scales
the whole structure. Strikes are passed explicitly so the caller controls the
exact shape (and so test reference values stay hand-computable).
"""
from lab.strategy.legs import Leg, Strategy


def covered_call(stock_entry, call_strike, call_premium, expiry, qty=1):
    """Long the underlier, short an upside call against it."""
    return Strategy([
        Leg("stock", quantity=qty, premium=stock_entry, expiry=expiry),
        Leg("call", quantity=-qty, strike=call_strike, premium=call_premium, expiry=expiry),
    ])


def vertical_spread(kind, long_strike, short_strike, long_premium, short_premium, expiry, qty=1):
    """Long one option, short another of the same kind/expiry at a different strike."""
    return Strategy([
        Leg(kind, quantity=qty, strike=long_strike, premium=long_premium, expiry=expiry),
        Leg(kind, quantity=-qty, strike=short_strike, premium=short_premium, expiry=expiry),
    ])


def straddle(strike, call_premium, put_premium, expiry, qty=1):
    """Long a call and a put at the same strike (long volatility)."""
    return Strategy([
        Leg("call", quantity=qty, strike=strike, premium=call_premium, expiry=expiry),
        Leg("put", quantity=qty, strike=strike, premium=put_premium, expiry=expiry),
    ])


def strangle(call_strike, put_strike, call_premium, put_premium, expiry, qty=1):
    """Long an OTM call and an OTM put at different strikes."""
    return Strategy([
        Leg("call", quantity=qty, strike=call_strike, premium=call_premium, expiry=expiry),
        Leg("put", quantity=qty, strike=put_strike, premium=put_premium, expiry=expiry),
    ])


def iron_condor(
    long_put_strike,
    short_put_strike,
    short_call_strike,
    long_call_strike,
    long_put_premium,
    short_put_premium,
    short_call_premium,
    long_call_premium,
    expiry,
    qty=1,
):
    """Short put spread + short call spread — a defined-risk short-premium play."""
    return Strategy([
        Leg("put", quantity=qty, strike=long_put_strike,
            premium=long_put_premium, expiry=expiry),
        Leg("put", quantity=-qty, strike=short_put_strike,
            premium=short_put_premium, expiry=expiry),
        Leg("call", quantity=-qty, strike=short_call_strike,
            premium=short_call_premium, expiry=expiry),
        Leg("call", quantity=qty, strike=long_call_strike,
            premium=long_call_premium, expiry=expiry),
    ])


def calendar(strike, kind, near_premium, far_premium, near_expiry, far_expiry, qty=1):
    """Short a near-dated option, long a far-dated one at the same strike.

    Spans two expiries, so read it through `Strategy.mark_to_model`; the
    single-expiry at-expiry methods will refuse it by design.
    """
    return Strategy([
        Leg(kind, quantity=-qty, strike=strike, premium=near_premium, expiry=near_expiry),
        Leg(kind, quantity=qty, strike=strike, premium=far_premium, expiry=far_expiry),
    ])
