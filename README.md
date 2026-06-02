# Options Lab

An equities-and-options strategy studio — payoff, Greeks, IV surface, and an honest walk-forward + Monte-Carlo backtest — built to show the trade you *decided not to put on*, not just a green equity curve.

> **Status:** scaffolded (spec + plan in place). Build follows `PLAN.md` (M0 → M9).
> **Not financial advice.** Analytics / education tool on public + simulated data. No live trading, no brokerage, no real money, no personal account data.

Part of [hector-garza.com](https://hector-garza.com)'s portfolio. One of three equal deliverables: the app, a **Decision Record** ([`DECISIONS.md`](./DECISIONS.md)), and a recorded whiteboard session. A working demo no longer proves competence — the judgment behind it does. See [`SPEC.md`](./SPEC.md) §0.

## What it does
- Build a multi-leg options strategy (covered call, vertical, condor, calendar) → payoff, breakevens, max profit/loss, P(profit).
- Net **Greeks** (delta/gamma/theta/vega/rho), implied-vol **surface**, skew, term structure.
- A **regime filter** that can say *"sit out."*
- **Walk-forward + Monte-Carlo backtest** with an explicit cost model and a with/without-costs toggle.
- Risk-based position sizing (tail-survival, not growth-max).

## Tech stack
- **Backend:** Django (views over framework-free quant modules)
- **Quant:** NumPy / SciPy / pandas; `yfinance` for historical bars
- **Frontend:** Django templates + HTMX + Plotly
- **Packaging:** Docker · **Quality:** pytest + ruff + GitHub Actions CI

## Deployment
- **Live demo:** Dockerized Django app on **Render**, fronted by **Cloudflare** (planned subdomain `options.hector-garza.com`). No API keys (yfinance is keyless).
- Local run: one command via Docker (added in build step M0).

## Links (filled in as the build progresses)
- 🔗 Live demo: _TBD_
- 🧠 Decision record: [`DECISIONS.md`](./DECISIONS.md)
- 🎥 Whiteboard walkthrough: _TBD_

## Build
See [`PLAN.md`](./PLAN.md) — M0 (scaffold) → M9 (decision record + whiteboard). The pure quant core (pricing/Greeks/IV/backtest) is built test-first.
