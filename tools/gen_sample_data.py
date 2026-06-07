"""Generate the seeded, *simulated* sample bars shipped for offline demos.

Reproducible (fixed seed) so the committed CSVs are auditable. This is
illustrative data, not real market history — labeled as such per the
project's honesty-about-data stance (SPEC.md §5).

Run from the repo root:  python tools/gen_sample_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "lab" / "data" / "sample"

# (ticker, seed, start_price, annual drift, annual vol)
SERIES = [
    ("SPY", 20240101, 450.0, 0.08, 0.16),
    ("AAPL", 20240102, 180.0, 0.12, 0.28),
]

DAYS = 504          # ~2 years of business days
TRADING_DAYS = 252


def simulate_ohlcv(seed, start_price, mu, sigma):
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    shocks = rng.standard_normal(DAYS)
    log_steps = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shocks
    close = start_price * np.exp(np.cumsum(log_steps))

    # Plausible OHLC around each close; volume as a noisy positive series.
    intraday = sigma * np.sqrt(dt) * close
    open_ = np.empty(DAYS)
    open_[0] = start_price
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + np.abs(rng.standard_normal(DAYS)) * intraday
    low = np.minimum(open_, close) - np.abs(rng.standard_normal(DAYS)) * intraday
    volume = (rng.lognormal(mean=16.0, sigma=0.3, size=DAYS)).round()

    idx = pd.bdate_range("2022-01-03", periods=DAYS, name="date")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    ).round(4)


def main():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    for ticker, seed, price, mu, sigma in SERIES:
        df = simulate_ohlcv(seed, price, mu, sigma)
        df.to_csv(SAMPLE_DIR / f"{ticker}.csv", index_label="date")
        print(f"wrote {ticker}: {len(df)} bars -> {SAMPLE_DIR / f'{ticker}.csv'}")


if __name__ == "__main__":
    main()
