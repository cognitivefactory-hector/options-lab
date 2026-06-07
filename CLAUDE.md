# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Options Lab — an equities/options strategy studio (payoff, Greeks, IV surface, walk-forward + Monte-Carlo backtest). It is a **job-search portfolio project**, and that framing drives every design choice: the goal is to demonstrate *trading judgment* (knowing when there's no edge, sizing so a tail event doesn't end you), **not** to ship a green equity curve or a signal generator.

**Three deliverables of equal weight** (see `SPEC.md` §0):
1. The working app.
2. `DECISIONS.md` — the Situation/Decision/Risk/Change decision record.
3. A recorded whiteboard session defending risk/robustness choices.

Treat `DECISIONS.md` as a first-class artifact, not an afterthought. When you make a non-obvious engineering or quant decision (especially what you *rejected* or *consciously accepted*), record it there while the reasoning is alive. Milestone M9 — the decision record + whiteboard — is the differentiator; never treat the project as "done" just because the app runs.

## Current state

M0 done. The Django scaffold serves a landing page (with the disclaimer) locally and via Docker/gunicorn; pytest + ruff + GitHub Actions CI are wired up. The quant core (`pricing/`, `vol/`, `strategy/`, `backtest/`, `regime/`, `sizing/`, `data/`) does not exist yet — M1 (pricing + Greeks, test-first) is next.

`PLAN.md` is the authoritative build sequence (M0 → M9): scaffold → pricing/Greeks → IV solver/surface → strategy builder → **backtest+costs+Monte-Carlo (the trust core)** → regime+sizing → data layer → UI → deploy → decision record/whiteboard. Read it before starting any milestone.

## Architecture (intended)

The core principle: **a pure, framework-free quant core, with Django as a thin view layer over it.**

- The math lives in plain-Python modules (planned under `lab/`): `pricing/` (Black-Scholes price + analytic Greeks), `vol/` (IV solver, surface/skew/term structure), `strategy/` (multi-leg payoff, breakevens, P(profit)), `backtest/` (`walkforward.py`, `costs.py`, `montecarlo.py`, `metrics.py`), `regime/`, `sizing/`, `data/` (yfinance fetch + cache + CSV fallback).
- These modules must not import Django. Django `views.py` calls them and returns JSON; the frontend is Django templates + HTMX + Plotly.
- Libraries: numpy, pandas, scipy, yfinance, plotly. No ML framework — there is **no price prediction** here by design.
- No DB required for the math (cache to disk); SQLite only if persisting runs.

## How to build the quant core

**Build the quant core test-first.** Pricing, Greeks, IV, and the backtest are pure deterministic functions — write tests before implementation. Don't chase UI test coverage (the UI is demonstrated by the whiteboard recording).

Golden invariants the tests must enforce (these are non-negotiable correctness anchors):
- Put-call parity holds within tolerance.
- IV round-trips: price → IV → price recovers the input vol.
- **Costs always strictly reduce net return** — "with costs" < "without costs" on the same data, always.
- Capped/fractional Kelly never goes full Kelly.
- The regime filter can and does output **"sit out"** on the right fixture (this is a feature, not a missing trade).

## Non-negotiable constraints

- **Never add live trading, broker integration, order routing, real-money execution, or personal account/position data.** These are explicit forbidden non-goals (`SPEC.md` §4.4), not just out-of-scope.
- **Honesty about data is part of the product.** Where real historical option chains aren't available, option prices are reconstructed from the underlier path + a Black-Scholes vol assumption — this **must be labeled a model approximation** in the UI, README, and `DECISIONS.md`. Keep clear which results depend on the BS reconstruction vs. real data.
- The **regime filter is defined a priori** (realized-vol percentile / term structure), specified before fitting — never tuned after seeing backtest results.
- The **"not financial advice" disclaimer** must stay prominent in the footer and README.
- Backtests use **walk-forward (rolling in-sample → out-of-sample)** only — never report a single in-sample fit. Always report the outcome *distribution* (Monte Carlo), not one path.

## Commands

Local dev uses a venv; `make` targets wrap the common ones.

- Install dev deps: `pip install -r requirements-dev.txt` (or `make install`)
- Tests: `pytest` / `make test` (single test: `pytest tests/test_pricing.py::test_name`)
- Lint: `ruff check .` / `make lint`  · format: `ruff format .` / `make fmt`
- Run app (Docker, one command): `make run` (= `docker compose up --build`) → http://localhost:8000
- Run app (no Docker): `python manage.py runserver`
- Health check: `GET /healthz` → `{"status": "ok"}`

The Django project is `config/`; the app is `lab/`. Settings read from the environment (see `.env.example`) so one image runs locally and on Render. CI (`.github/workflows/ci.yml`) runs `ruff check` + `pytest` on push/PR.
