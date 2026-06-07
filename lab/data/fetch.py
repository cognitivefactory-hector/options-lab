"""Historical daily bars: yfinance fetch, on-disk cache, offline sample.

Resolution order for `load_bars` (robust for a live demo):
  1. on-disk cache (a CSV we wrote earlier) — fast and offline;
  2. live fetch via the injected `fetcher` (yfinance by default) → cached;
  3. the seeded **sample** shipped in the repo — so the demo still runs with
     the network off or the API flaky.

yfinance is keyless and imported lazily, so nothing here touches the network
(or even requires yfinance) until a live fetch is actually attempted; tests
inject a fake fetcher and never hit it. The shipped sample is **simulated /
illustrative** data (see lab/data/sample/README.md) — labeled, per the
project's honesty-about-data stance.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]
SAMPLE_TICKERS = ("SPY", "AAPL")

SAMPLE_DIR = Path(__file__).resolve().parent / "sample"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / "cache"


def to_csv(df: pd.DataFrame, path) -> None:
    """Write a bars frame (date index + OHLCV columns) to CSV."""
    df.to_csv(path, index_label="date")


def from_csv(path) -> pd.DataFrame:
    """Read a bars frame back, parsing the date index."""
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    df.index.name = "date"
    return df[OHLCV_COLUMNS]


def closes(df: pd.DataFrame) -> np.ndarray:
    """Close prices as a 1-D float array (what the quant core consumes)."""
    return df["close"].to_numpy(dtype=float)


def fetch_yfinance(ticker, start=None, end=None) -> pd.DataFrame:
    """Download daily bars from yfinance and normalize to the OHLCV schema."""
    import yfinance as yf  # lazy: keeps the network/dep out of import time

    raw = yf.download(ticker, start=start, end=end, interval="1d",
                      auto_adjust=True, progress=False)
    if raw.empty:
        raise RuntimeError(f"no data returned for {ticker!r}")
    # yfinance may return a column MultiIndex for a single ticker; flatten it.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw.rename(columns=str.lower)[OHLCV_COLUMNS]
    df.index.name = "date"
    return df


def load_sample(ticker) -> pd.DataFrame:
    """Load a shipped sample series (offline, reproducible)."""
    path = SAMPLE_DIR / f"{ticker}.csv"
    if not path.exists():
        raise FileNotFoundError(f"no sample for {ticker!r} at {path}")
    return from_csv(path)


def load_bars(ticker, *, cache_dir=DEFAULT_CACHE_DIR, fetcher=None,
              start=None, end=None, use_cache=True) -> pd.DataFrame:
    """Load daily bars via cache → live fetch → seeded sample.

    `fetcher` is injectable (defaults to yfinance) so callers and tests can run
    fully offline. A successful live fetch is cached for next time.
    """
    cache_dir = Path(cache_dir)
    cache_path = cache_dir / f"{ticker}.csv"

    if use_cache and cache_path.exists():
        return from_csv(cache_path)

    if fetcher is None:
        fetcher = fetch_yfinance
    try:
        df = fetcher(ticker, start, end)
        cache_dir.mkdir(parents=True, exist_ok=True)
        to_csv(df, cache_path)
        return df
    except Exception:
        # Live data unavailable — fall back to the shipped sample if we have one.
        sample_path = SAMPLE_DIR / f"{ticker}.csv"
        if sample_path.exists():
            return from_csv(sample_path)
        raise FileNotFoundError(
            f"no cache, live fetch failed, and no sample for {ticker!r}"
        ) from None
