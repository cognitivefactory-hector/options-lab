# Options Lab — Implementation Plan

Companion to `SPEC.md`. The build sequence: milestones, concrete tasks, acceptance criteria, and the definition of done. Self-contained — hand this repo to a fresh session and start.

- **Repo:** `options-lab` (public, under `cognitivefactory-hector`)
- **Approach:** build the **pure quant core (pricing, Greeks, IV, backtest) test-first**, then the regime filter and sizing, then the UI. The math is the foundation; get it provably right before drawing charts.

> **Not financial advice.** Analytics/education only. No live trading, no broker, no real money, no personal account data. Keep the disclaimer in the footer and README.

---

## The spine (carry through every milestone)

Keep `DECISIONS.md` open and capture reasoning live:

> **Situation** · **Decision** (incl. what you *rejected* — the "signal generator" framing and curve-fitting) · **Risk** (incl. what you *accepted* — growth-for-survivability) · **Change**.

The hardest decisions (robustness over backtest-return; tail-survival sizing; "sit out" as a valid output) are the spine of the **recorded whiteboard session** — see `SPEC.md` §3.

---

## Prerequisites
- Python 3.11+, Docker, a GitHub account (`gh` authenticated).
- No API keys (yfinance is keyless). Internet for data fetches, with a CSV fallback for offline demos.

---

## Milestones

### M0 — Repo scaffold *(½ day)*
- [ ] Folder + `SPEC.md` + `PLAN.md`.
- [ ] `README.md` (stub with disclaimer), `DECISIONS.md` (paste template from `SPEC.md` §10), `.gitignore` (Python + `data/cache/`), `LICENSE` (MIT).
- [ ] `pyproject.toml`/`requirements.txt`, `Dockerfile`, `make run` (or `docker compose up`) serving an empty Django page.
- [ ] `gh repo create … --public --push`.
- **Acceptance:** app serves a page; repo on GitHub; disclaimer present.

### M1 — Pricing + Greeks (pure, TDD) *(1–2 days)*
**Goal:** a tested, framework-free pricing core.
- [ ] `pricing/black_scholes.py`: price + analytic **delta, gamma, theta, vega, rho** for calls/puts.
- [ ] **Tests first:** known textbook values (put-call parity holds; ATM Greeks in expected ranges; Greeks have correct signs).
- **Acceptance:** `pytest` green; put-call parity test passes within tolerance.

### M2 — IV solver + surface *(1 day)*
- [ ] `vol/iv.py`: solve implied vol from price (bisection/Newton) with graceful no-solution handling.
- [ ] `vol/surface.py`: build a strike × expiry grid; expose skew and term structure.
- [ ] Tests: round-trip (price → IV → price) recovers input vol; monotonic/edge cases handled.
- **Acceptance:** `pytest` green; round-trip IV recovers vol within tolerance.

### M3 — Strategy builder (pure) *(1 day)*
- [ ] `strategy/legs.py`: multi-leg position; payoff at expiry + mark-to-model; breakevens; max profit/loss; net Greeks; P(profit) via lognormal.
- [ ] Presets: covered call, vertical spread, straddle/strangle, iron condor, calendar.
- [ ] Tests: each preset's max-loss / breakevens match hand-computed values.
- **Acceptance:** `pytest` green; iron-condor breakevens and max loss verified by hand.

### M4 — Backtest engine with costs + Monte Carlo (TDD) *(2–3 days)* — **the trust core**
- [ ] `backtest/walkforward.py`: rolling in-sample → out-of-sample; **no single in-sample fit.**
- [ ] `backtest/costs.py`: commission, slippage, bid/ask spread, assignment; a **with/without-costs toggle.**
- [ ] `backtest/montecarlo.py`: GBM path simulation → outcome + drawdown distribution.
- [ ] Where real option series are unavailable, reconstruct option prices from the underlier path + BS vol — **and label it a model approximation** (record in `DECISIONS.md`).
- [ ] Metrics: CAGR, max drawdown, Sharpe, Sortino, win rate, profit factor.
- [ ] **Tests:** costs strictly reduce net return; a known path yields expected P&L; Monte-Carlo summary stats are stable with a fixed seed.
- **Acceptance:** `pytest` green; "with costs" net return < "without costs" on the same data, always.

### M5 — Regime filter + sizing *(1 day)*
- [ ] `regime/vol_regime.py`: realized-vol percentile + term-structure read → **favorable / neutral / sit-out** verdict, defined a priori.
- [ ] `sizing/risk.py`: fixed-fractional + capped/fractional-Kelly; surface the tail-survival rationale.
- [ ] Tests: a high-vol/unfavorable regime returns "sit out"; Kelly is capped (never full).
- **Acceptance:** `pytest` green; the filter can and does say "sit out" on the right fixture.

### M6 — Data layer *(½–1 day)*
- [ ] `data/fetch.py`: yfinance daily bars + on-disk cache + **CSV fallback** for offline/demo.
- [ ] Ship a seeded sample (1–2 tickers) so the demo is reproducible without a live API.
- **Acceptance:** demo runs from the cached sample with the network off.

### M7 — UI: Builder / Vol / Backtest tabs *(2 days)*
- [ ] Builder: underlier + legs → payoff diagram, Greeks, breakevens, **regime verdict**.
- [ ] Vol: IV surface (or skew + term-structure pair), labeled if illustrative.
- [ ] Backtest: equity curve **with vs. without costs**, drawdown, Monte-Carlo fan chart, metrics table.
- [ ] Footer disclaimer: "Not financial advice. Public/simulated data; no live trading."
- **Acceptance:** open URL, build an iron condor, see Greeks + payoff, run a backtest, watch costs eat into it, see a "sit-out" regime example.

### M8 — Polish, README, deploy *(1 day)*
- [ ] `README.md`: what/why, one-command run, screenshots/GIF, links to live demo + `DECISIONS.md` + whiteboard video; disclaimers prominent.
- [ ] Deploy (Render/Railway/Fly/VPS); smoke-test; optional `options.hector-garza.com`.
- **Acceptance:** public URL works from a fresh browser.

### M9 — Decision Record + Whiteboard session *(½ day)* — **do not skip; this is the differentiator**
- [ ] Complete `DECISIONS.md` (Situation/Decision/Risk/Change; rejected "signal generator"; accepted growth-for-survivability).
- [ ] Record the 5–8 min whiteboard session using `SPEC.md` §3.1 — make sure to walk the **declined-trade** example (challenge #5).
- [ ] Embed/link the recording in README and on hector-garza.com.
- **Acceptance:** a stranger can read `DECISIONS.md` + watch the video and explain *why you'd sit a trade out.*

---

## Testing strategy
- **The quant core is the crown jewel — test it hard and first.** Pricing/Greeks/IV/backtest are pure functions; deterministic with seeds.
- Golden invariants: put-call parity; IV round-trip; costs always reduce net return; capped Kelly never goes full.
- UI is demonstrated by the recording; don't chase UI coverage.

## Suggested repo layout
```
options-lab/
├── README.md  SPEC.md  PLAN.md  DECISIONS.md
├── Dockerfile  pyproject.toml  manage.py
├── config/  settings.py  urls.py            # Django project
├── lab/                       # the Django app (views/JSON endpoints)
│   ├── views.py              # compute endpoints calling the pure modules below
│   ├── pricing/  black_scholes.py            # framework-free, TDD'd
│   ├── vol/      iv.py surface.py
│   ├── strategy/ legs.py presets.py
│   ├── backtest/ walkforward.py costs.py montecarlo.py metrics.py
│   ├── regime/   vol_regime.py
│   ├── sizing/   risk.py
│   ├── data/     fetch.py  cache/  sample/
│   └── templates/  index.html   ( + HTMX / Plotly, static/ )
└── tests/ test_pricing.py test_iv.py test_strategy.py test_backtest_costs.py test_regime.py
```

## Risk register (project execution)
| Risk | Mitigation |
|---|---|
| Backtest looks great but is overfit / data-snooped | Walk-forward + out-of-sample + Monte Carlo; never report a single in-sample fit. |
| Ignoring costs makes results a fantasy | Cost model is mandatory; UI shows with/without; a test enforces costs reduce return. |
| Reconstructed option prices mistaken for real | Label the approximation in UI + README + `DECISIONS.md`; be the one who flags it. |
| Looks like trading advice / a product | Disclaimer in footer + README; non-goals forbid live trading and account data. |
| Regime filter is secretly another tuned knob | Define it a priori, before fitting; defend the logic in the whiteboard session. |
| Skipping M9 because the app "looks done" | M9 *is* the portfolio. The declined-trade story is the whole point. |

## Definition of Done
See `SPEC.md` §8 — all three deliverables (app, decision record, whiteboard recording) exist and are linked from the README, costs visibly matter, and the regime filter demonstrably outputs "sit out."
