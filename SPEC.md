# Options Lab — Design Spec

**Project 3 of the Hector Garza portfolio.** Self-contained: everything needed to start this as its own repository is in this file and its companion `PLAN.md`. You do not need any other file from the `career/` folder to build this.

- **Owner:** Hector Garza · hectorg@smartxchain.com · hector-garza.com
- **Status:** Spec — ready to build
- **Suggested repo name:** `options-lab`
- **One-liner:** An equities-and-options strategy studio — payoff, Greeks, IV surface, and an honest walk-forward + Monte-Carlo backtest — built to show the trade you *decided not to put on*, not just a green equity curve.

> **Not financial advice.** This is an analytics / education tool using public and simulated data. No live trading, no brokerage, no real-money execution, no personal account data. The UI and README say so plainly.

---

## 0. Read this first — what this project is *really* for

This is a job-search portfolio project, but it is **not** a "look, my backtest is up 200%" demo. Anyone can produce a green curve with hindsight and a few tuned parameters — that proves nothing. The hireable signal is **trading judgment**: knowing when the edge *isn't* there, sizing so a tail event doesn't end you, and being honest about what a backtest can and can't prove.

So this project has **three deliverables of equal weight**:

1. **The working app** (hosted, clickable).
2. **A Decision Record** (`DECISIONS.md`) structured around the four questions below.
3. **A recorded whiteboard session** (5–8 min) where you defend your risk and robustness choices against push-back.

A hiring manager who opens this repo should learn that you think in *risk and regimes*, not lottery tickets.

---

## 1. The spine — four questions that make judgment portable

Every project in this portfolio is organized around these four questions. They appear here, in `DECISIONS.md`, and on the project's page at hector-garza.com. Fill them in *as you build*, while the reasoning is still alive.

> **1 · Situation** — What's happening, who's involved, the constraints, the facts you have and the facts that are *missing*. Context is where judgment begins.
>
> **2 · Decision** — The plausible paths, the one you took, and the credible options you *rejected*. Rejection shows what you refused to hand-wave.
>
> **3 · Risk** — What could go wrong, what you removed, and what you *consciously accepted*. Prevented losses count — name the bad outcome that didn't happen.
>
> **4 · Change** — What's different now: clearer, safer, faster. Connect the judgment to a real change in the work, not a diary entry.

### 1.1 First-draft answers for Options Lab (defend/revise these on camera)

These are your starting position. The whiteboard session (§3) exists to pressure-test them — and you trade equities and options for real, so these are *your* judgments, not borrowed ones.

- **Situation.** You trade equities and options on your own time. Almost every retail tool sells a strategy by showing a green equity curve and hiding the conditions where the edge evaporates — the regime where a short-premium strategy gets run over, the costs that quietly eat the alpha. The hard, valuable skill isn't *generating* a strategy; it's deciding **whether the regime even justifies the trade**, and **sizing so a tail event doesn't end you.** Facts you have: historical underlier prices and option pricing models. Facts you're missing: deep, clean historical options data (free retail data is thin and delayed) and, of course, the future regime.
- **Decision.** Build a studio that makes the *decision process* legible: payoff + Greeks + IV surface to understand the position; a **regime filter that can say "don't trade"**; a **walk-forward + Monte-Carlo backtest** that tests robustness instead of chasing the best in-sample return; and **risk-based position sizing.** **You rejected the "signal generator / auto-buy-button" framing** — the point is visible judgment, not a black box. **You rejected optimizing for peak backtest return** (curve-fitting) in favor of parameter stability and out-of-sample honesty.
- **Risk.** The killer risk is **fooling yourself**: an overfit backtest, ignored transaction costs / slippage / assignment, and a short-vol strategy that looks great until the tail event that ends the account. Mitigations: out-of-sample walk-forward, modeled costs, Monte-Carlo'd drawdowns, and sizing to **survive a fat tail rather than maximize growth (no Kelly-max).** You *consciously accept lower headline returns for survivability* — you refuse ruin risk.
- **Change.** Positions are sized to risk, not conviction; you can point to the **trades you didn't take** because the regime was wrong; and the backtest is honest about what it proves. The prevented loss: the blow-up that didn't happen because you sat out or sized down.

---

## 2. Why this project (market fit)

- It's your **genuine edge and your "I do this on my own time" story** — credibility a manager can feel.
- Demonstrates real quant fundamentals employers screen for: options pricing & Greeks, implied vol / surface / skew, regime awareness, and **robust backtesting** (walk-forward, Monte Carlo) — the retail-quant skill stack (QuantConnect/Backtrader ecosystem).
- It's the clearest place to show the portfolio thesis: **judgment over generation.** The differentiated artifact is literally "the trade I declined."
- Rounds out the portfolio beyond manufacturing, showing range without diluting focus.

---

## 3. The staged whiteboard session (recorded deliverable)

**Format.** 5–8 minutes. Screen + voice (Loom, or OBS → MP4), at the "whiteboard" (a payoff/IV chart, or the running app), defending the design while an adversary pushes back. Use a strong quant-literate friend, or answer the scripted challenges below on camera as if in an interview. Preserve the surviving reasoning in `DECISIONS.md`.

**The point is not a perfect backtest.** It's showing you can defend robustness and risk under pressure, and concede a fair point without going mushy.

### 3.1 Adversarial challenge script (the push-back)

1. **"Every backtest looks great in hindsight. How do I know this isn't curve-fit or data-snooped?"**
   *(Defend walk-forward / out-of-sample, parameter-stability checks, and Monte-Carlo of outcomes — not a single lucky path.)*
2. **"You're using free, delayed data with thin options chains. Garbage in, garbage out — so why trust any of it?"**
   *(Be honest about data limits; explain what you model vs. what you'd need real data for; show you know the difference.)*
3. **"Where are transaction costs, slippage, bid/ask, and assignment? Retail backtests ignore these and die live."**
   *(Defend an explicit cost model; show how results degrade once costs are in — and that you *want* to see that.)*
4. **"Your regime filter is just another knob you tuned to make the curve nicer. Justify it."**
   *(Tie the filter to an a-priori volatility logic — e.g., realized-vol percentile / term-structure — defined before fitting, not optimized after.)*
5. **"Show me the trade you DIDN'T take. Anyone can show winners."**
   *(This is the core thesis. Walk through a regime where the tool says "sit out" and why that's the valuable output.)*
6. **"Defend your position sizing. Kelly blows up; fixed-fractional is naive."**
   *(Risk-based sizing to survive a tail; the explicit trade of growth for survivability.)*

### 3.2 What the recording must show
- The **Situation → Decision → Risk → Change** arc (§1.1), in your words.
- A concrete **"don't trade / size down" example** — the declined trade.
- At least one place you **revised** under push-back (or a crisp reason you held).
- A pointer to where the surviving reasoning lives (`DECISIONS.md`).

---

## 4. Product specification

### 4.1 Users
- **Primary:** you (and a quant-literate peer) reasoning about a position before risking capital.
- **Demo viewer:** a hiring manager who must "get it" in 60 seconds and see risk-first thinking.

### 4.2 Core features (MVP)
1. **Strategy builder.** Pick an underlier (ticker) and assemble a multi-leg position: covered call, vertical spread, straddle/strangle, iron condor, calendar. Per-leg strike / expiry / qty / side.
2. **Payoff & metrics.** Payoff diagram at expiry (and mark-to-model before expiry), breakevens, max profit / max loss, and probability-of-profit from a lognormal model.
3. **Greeks.** Per-leg and net **delta, gamma, theta, vega, rho**, recomputed as inputs change.
4. **Implied-vol tools.** Solve IV from option prices; render an **IV surface** (strike × expiry) and show **skew** and **term structure**.
5. **Regime panel (the judgment hook).** A volatility-regime read (e.g., realized-vol percentile, term-structure contango/backwardation) that **renders a clear "favorable / neutral / sit-out" verdict** for the chosen strategy type.
6. **Backtest.** **Walk-forward** over historical data with an explicit **cost model** (commission, slippage, bid/ask, assignment), plus a **Monte-Carlo** simulation (GBM paths) of the outcome distribution. Report CAGR, max drawdown, Sharpe/Sortino, win rate, profit factor — and the distribution, not just the mean.
7. **Position sizing.** Risk-based sizing (fixed-fractional and a capped/fractional-Kelly option) with the tail-survival rationale shown.

### 4.3 Screens
- **Builder** (default): underlier + legs → payoff, Greeks, breakevens, regime verdict.
- **Vol** : IV surface, skew, term structure.
- **Backtest** : walk-forward equity curve **with and without costs**, drawdown, Monte-Carlo fan chart, metrics.
- **About / Decision Record** (or link to hector-garza.com): the SDRC story + embedded whiteboard recording.

### 4.4 Explicit non-goals (YAGNI)
- **No live trading, no broker integration, no order routing, no real money.** Ever.
- No personal account / position data.
- No intraday tick data or HFT; daily bars are enough.
- No ML price prediction — the substance is options analytics and honest backtesting, not a crystal ball.
- No accounts/multi-tenant; a demo session is enough.

---

## 5. Data (public + simulated — be honest about limits)

- **Underlier prices:** historical daily bars via `yfinance` (or a CSV fallback so the demo works offline / when the API is flaky).
- **Options data:** free retail options chains are thin and delayed — **say so.** For pricing and Greeks, compute from Black-Scholes using the underlier + a vol input. For the IV surface, use available chain snapshots where present, and clearly label simulated/illustrative surfaces where not.
- **Backtest options series:** where real historical option prices aren't available, **reconstruct option prices from the underlier path + a vol assumption via Black-Scholes**, and disclose that this is a model approximation (a known, defensible simplification — name it in `DECISIONS.md`).
- Cache fetched data; ship a seeded sample (e.g., a couple of tickers) so demos are reproducible and don't depend on a live API.

> The honesty about data limitations is itself part of the judgment story — auditors and quant interviewers both reward it.

---

## 6. Architecture & stack

Chosen to match the owner's stack and to host cleanly as a live demo.

```
┌──────────────────────────────────────────────────────────┐
│  Browser — Builder / Vol / Backtest tabs                    │
│   • Plotly charts (payoff, IV surface, equity curve, MC fan) │
│   • REST calls to compute pricing/Greeks/backtest            │
└───────────────▲──────────────────────────┬──────────────────┘
                │ JSON                       │
┌───────────────┴──────────────────────────▼──────────────────┐
│  Backend — Django                                             │
│   • pricing/        Black-Scholes, Greeks, IV solver          │
│   • strategy/       multi-leg payoff, breakevens, P(profit)   │
│   • vol/            IV surface, skew, term structure          │
│   • regime/         realized-vol percentile, term structure   │
│   • backtest/       walk-forward + cost model + Monte Carlo    │
│   • data/           yfinance fetch + cache + CSV fallback     │
└───────────────────────────────────────────────────────────────┘
```

**Backend:** **Django** (views/JSON endpoints calling the pure-Python modules) — one framework across the whole portfolio; front end is **Django templates + HTMX + Plotly**. The well-tested `pricing/`, `strategy/`, and `backtest/` modules are framework-free and the core — easy and important to TDD. No DB needed for the math (cache to disk); add SQLite only to persist runs.

**Libraries:** `numpy`, `pandas`, `scipy` (optimize/stats for the IV solver and distributions), `yfinance`, `plotly`. Keep it lean; no ML framework needed.

---

## 7. Quant substance (get it right — you'll be asked about it)

- **Pricing:** Black-Scholes for European options; payoff at expiry and mark-to-model before. Document the assumptions (constant vol, no early exercise) and where they break (American options, dividends).
- **Greeks:** analytic delta, gamma, theta, vega, rho; net them across legs.
- **Implied vol:** solve via bisection or Newton-Raphson with a sane initial guess; handle no-solution cases gracefully.
- **IV surface / skew / term structure:** strike × expiry grid; show the smile/skew and the term structure; explain what a steep skew implies.
- **Backtest discipline (the part that earns trust):**
  - **Walk-forward** (rolling in-sample → out-of-sample), never a single in-sample fit.
  - **Explicit cost model:** commission, slippage, bid/ask spread, assignment — and a toggle to show results *with vs. without* costs.
  - **Monte Carlo:** simulate many GBM paths to get an *outcome distribution* and drawdown distribution — not one lucky history.
  - **Metrics:** CAGR, max drawdown, Sharpe, Sortino, win rate, profit factor; report the distribution and the tail.
- **Regime filter:** defined a priori (e.g., trade short-premium only when realized-vol percentile and term structure are favorable); it must be able to output **"sit out."**
- **Sizing:** fixed-fractional and capped/fractional-Kelly; show the tail-survival reasoning, not growth maximization.

---

## 8. Definition of Done

Portfolio-ready when **all three** exist and are linked together:

- [ ] **App** deployed at a public URL: build a strategy → see payoff/Greeks/IV → run a walk-forward backtest with a costs toggle and a Monte-Carlo fan → see the regime verdict (including a "sit-out" case).
- [ ] **`README.md`** — what/why, one-command local run (Docker), screenshots/GIF, links to live demo + `DECISIONS.md` + whiteboard video, **and the not-financial-advice + data-limitations disclaimers.**
- [ ] **`DECISIONS.md`** — the §1 four-question template completed, including the rejected "signal generator" framing and the accepted growth-for-survivability trade.
- [ ] **Whiteboard recording** (5–8 min) linked from README and embedded on hector-garza.com, including the declined-trade example.
- [ ] **Costs visibly matter:** the backtest shows the with-vs-without-costs gap.
- [ ] Tests pass for pricing, Greeks, the IV solver, and the backtest cost accounting (see `PLAN.md`).

---

## 9. Hosting / deployment
- Containerize (`Dockerfile`); the Django app runs anywhere (Render / Railway / Fly.io / VPS) behind Cloudflare. No DB strictly required (cache to disk); add SQLite only if you want to persist runs.
- Optional subdomain: `options.hector-garza.com`; link from the resume's future "Selected Work" section.
- Put the **not-financial-advice disclaimer in the footer and the README**, prominently.

---

## 10. Repo bootstrap (how to start this as its own repo)

```bash
mkdir options-lab && cd options-lab
cp /path/to/03-options-lab/SPEC.md .
cp /path/to/03-options-lab/PLAN.md .
# seed: README.md, DECISIONS.md (paste template below), .gitignore (python + data cache), LICENSE (MIT)

git init && git add -A && git commit -m "chore: scaffold options-lab (spec + plan)"
git branch -M main
gh repo create cognitivefactory-hector/options-lab --public --source=. --remote=origin --push
```

> PUBLIC repo. No API keys needed (yfinance is keyless). Keep the disclaimer visible; never publish personal account/position data.

### `DECISIONS.md` starter (paste into the new repo)

```markdown
# Decision Record — Options Lab

## Situation
<you trade for real; tools sell green curves and hide regime/costs; missing clean options data + the future regime>

## Decision
<payoff/Greeks/IV + regime filter + walk-forward/MC + risk sizing; the "signal generator" framing you REJECTED; curve-fitting you REJECTED>

## Risk
<fooling yourself: overfit, ignored costs, short-vol tail blow-up; out-of-sample + cost model + MC + tail-survival sizing; the growth-for-survivability trade you ACCEPTED>

## Change
<sized to risk not conviction; the trades you DIDN'T take; an honest backtest; the blow-up that didn't happen>

## Whiteboard session
- Recording: <link>
- The declined trade (regime said sit out): <…>
- What I revised under push-back: <…>
- What I held the line on, and why: <…>
```

---

## 11. Open questions to resolve in the plan
- Backtest scope first pass: which 1–2 strategies (e.g., short put / covered call vs. iron condor)?
- Reconstruct option prices from underlier + BS vol (simple, disclosed) vs. source any real historical chains.
- Plotly 3-D surface vs. a 2-D skew + term-structure pair for the vol view (simpler may read better).
- Cost-model defaults (commission/slippage/spread) — pick defensible numbers and cite the reasoning.
