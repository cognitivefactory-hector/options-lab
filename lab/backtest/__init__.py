"""Backtest engine — the trust core.

Walk-forward (out-of-sample) evaluation, an explicit cost model with a
with/without toggle, Monte-Carlo outcome distributions, and honest metrics.
Option prices are reconstructed from the underlier + a Black-Scholes vol
assumption where real chains aren't available — a labeled model approximation
(see engine.reconstruct_option_price and SPEC.md §5).
"""
