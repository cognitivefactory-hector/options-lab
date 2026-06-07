# Sample data — SIMULATED / ILLUSTRATIVE

These CSVs are **not real market history.** They are seeded, simulated daily
bars (geometric Brownian motion) used so the app and tests run offline and
reproducibly, without depending on a live API.

Regenerate with:

```bash
python tools/gen_sample_data.py
```

For real bars, `lab.data.fetch.load_bars(ticker)` fetches from yfinance (keyless)
and caches to disk; these samples are the offline fallback. Per the project's
honesty-about-data stance (SPEC.md §5), simulated data is always labeled as such.
