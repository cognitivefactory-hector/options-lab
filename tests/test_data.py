"""Data layer — yfinance bars with an on-disk cache and an offline sample.

Everything here runs offline: the live fetcher is injectable, so tests pass a
fake (or a deliberately failing one) and never touch the network. The M6
acceptance gate: the demo loads from the seeded sample with the network off.
"""
import numpy as np
import pandas as pd
import pytest

from lab.data.fetch import (
    OHLCV_COLUMNS,
    SAMPLE_TICKERS,
    closes,
    from_csv,
    load_bars,
    load_sample,
    to_csv,
)


def _fake_bars(n=30, start_price=100.0):
    # Plain DatetimeIndex (no freq) — the canonical form bars take once they've
    # round-tripped through CSV or come back from yfinance.
    idx = pd.DatetimeIndex(pd.date_range("2024-01-01", periods=n, freq="B"), name="date")
    idx.freq = None
    close = np.linspace(start_price, start_price + n, n)
    return pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )


# --- CSV round-trip ------------------------------------------------------

def test_csv_round_trip_preserves_bars(tmp_path):
    df = _fake_bars()
    path = tmp_path / "X.csv"
    to_csv(df, path)
    back = from_csv(path)
    pd.testing.assert_frame_equal(df, back)


# --- load_bars resolution order -----------------------------------------

def test_load_bars_reads_cache_without_fetching(tmp_path):
    df = _fake_bars()
    to_csv(df, tmp_path / "SPY.csv")

    def fetcher(*a, **k):
        raise AssertionError("fetcher must not be called when cache exists")

    out = load_bars("SPY", cache_dir=tmp_path, fetcher=fetcher)
    pd.testing.assert_frame_equal(out, df)


def test_load_bars_fetches_then_caches(tmp_path):
    calls = []

    def fetcher(ticker, start, end):
        calls.append(ticker)
        return _fake_bars()

    first = load_bars("NEW", cache_dir=tmp_path, fetcher=fetcher)
    assert calls == ["NEW"]
    assert (tmp_path / "NEW.csv").exists()

    # Second call hits the cache; a now-failing fetcher proves it isn't used.
    def boom(*a, **k):
        raise RuntimeError("network down")

    second = load_bars("NEW", cache_dir=tmp_path, fetcher=boom)
    pd.testing.assert_frame_equal(first, second)


def test_load_bars_falls_back_to_sample_when_fetch_fails(tmp_path):
    def boom(*a, **k):
        raise RuntimeError("network down")

    # Empty cache + failing fetch -> the seeded sample carries the demo.
    out = load_bars(SAMPLE_TICKERS[0], cache_dir=tmp_path, fetcher=boom)
    assert not out.empty
    assert list(out.columns) == OHLCV_COLUMNS


def test_load_bars_raises_when_nothing_is_available(tmp_path):
    def boom(*a, **k):
        raise RuntimeError("network down")

    with pytest.raises(FileNotFoundError):
        load_bars("NOT_A_REAL_SAMPLE", cache_dir=tmp_path, fetcher=boom)


# --- seeded sample (offline demo) ---------------------------------------

@pytest.mark.parametrize("ticker", SAMPLE_TICKERS)
def test_seeded_sample_loads_offline(ticker):
    df = load_sample(ticker)
    assert list(df.columns) == OHLCV_COLUMNS
    assert len(df) >= 250                       # ~1y+ of daily bars
    assert df.index.is_monotonic_increasing
    assert (df["close"] > 0).all()


def test_closes_returns_positive_array():
    arr = closes(load_sample(SAMPLE_TICKERS[0]))
    assert isinstance(arr, np.ndarray)
    assert arr.ndim == 1 and (arr > 0).all()
