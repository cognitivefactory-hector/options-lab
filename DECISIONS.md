# Decision Record — Options Lab

The four questions that make judgment portable. These are **first-draft answers** (from `SPEC.md` §1.1) — pressure-test and revise them in the recorded whiteboard session, then keep what survives.

## Situation
I trade equities and options on my own time. Almost every retail tool sells a strategy by showing a green equity curve and hiding the conditions where the edge evaporates — the regime where short premium gets run over, the costs that quietly eat the alpha. The hard, valuable skill isn't *generating* a strategy; it's deciding **whether the regime even justifies the trade** and **sizing so a tail event doesn't end me.** Facts I have: historical underlier prices and pricing models. Facts I'm missing: deep, clean historical options data (free retail data is thin/delayed) and the future regime.

## Decision
A studio that makes the *decision process* legible: payoff + Greeks + IV surface to understand the position; a **regime filter that can say "don't trade"**; a **walk-forward + Monte-Carlo backtest** that tests robustness instead of chasing peak in-sample return; and **risk-based position sizing.**
**Rejected:** the "signal generator / auto-buy-button" framing (the point is visible judgment, not a black box); and optimizing for peak backtest return (curve-fitting) over parameter stability and out-of-sample honesty.

## Risk
The killer is **fooling myself**: an overfit backtest, ignored transaction costs / slippage / assignment, and a short-vol strategy that looks great until the tail event that ends the account. Mitigations: out-of-sample walk-forward, a modeled cost toggle, Monte-Carlo'd drawdowns, and sizing to **survive a fat tail (no Kelly-max).**
**Consciously accepted:** lower headline returns for survivability — I refuse ruin risk.

## Change
Positions are sized to risk, not conviction; I can point to the **trades I didn't take** because the regime was wrong; the backtest is honest about what it proves. The prevented loss: the blow-up that didn't happen because I sat out or sized down.

## Whiteboard session
- Recording: _TBD_
- The declined trade (regime said sit out): _…_
- What I revised under push-back / held the line on: _…_

---

## Engineering decisions (recorded as built)
- **Backend:** Django (views over framework-free `pricing/`, `strategy/`, `backtest/` modules) — one stack across the portfolio. Front end: Django templates + HTMX + Plotly.
- **Data:** `yfinance` historical bars + CSV fallback; option prices reconstructed from underlier + Black-Scholes vol where real chains aren't available — **labeled as a model approximation.**
- **Host:** Render (Dockerized) behind Cloudflare. No API keys.
- **Disclaimer:** analytics/education, not financial advice — in footer + README.
- **Backtest reconstruction (M4):** every backtested option price flows through one function, `backtest.engine.reconstruct_option_price` (Black-Scholes on the underlier path + a vol assumption). This is the **disclosed model approximation** — it proves method, not a live edge. Keeping it in a single place makes the assumption auditable rather than scattered.
- **Cost model (M4):** explicit commission / bid-ask spread / slippage / assignment with a **with-vs-without toggle** (`cost_model=None`). Costs are non-negative by construction (strictly positive when a position trades), so "with costs" can never beat "without costs" — enforced by a test, not just intended. Defaults are modest retail numbers (~$0.65/contract, 1c half-spread, ~2bps slippage); **REJECTED** frictionless backtesting, which is how retail results die live.
- **Walk-forward (M4):** parameters fit on a rolling in-sample window, evaluated only on the next disjoint out-of-sample window — never a single in-sample fit. A test asserts the fitter never sees its own fold's future (no leakage). Monte-Carlo (seeded GBM) reports an outcome/drawdown **distribution**, not one lucky path.
- **Regime filter (M5):** the verdict (favorable / neutral / **sit-out**) is defined **a priori** in source from volatility logic — realized-vol percentile (is premium rich?) + a short/long realized-vol term-structure ratio (is vol spiking?) — with thresholds set *before* any backtest, not tuned to flatter a curve. **SIT_OUT is the deliberate output a curve-fitter would never add** because it cuts trade count; a test asserts the filter does emit it on a spiking/backwardated fixture. Targets short-premium (the representative case).
- **Sizing (M5):** fixed-fractional (risk ≤ a fixed % of capital per trade; floors to whole contracts, so it can size to **zero** — "don't trade") and **capped/fractional Kelly**. Full Kelly is **REJECTED** — it blows up on a fat tail; we always take a fraction of Kelly and cap it (a test enforces "never full"), and a non-positive edge sizes to 0. The conscious trade **ACCEPTED**: lower growth for tail survival.
- **Data layer (M6):** `load_bars` resolves cache → live yfinance fetch → shipped sample, with the fetcher **injectable** so the app and tests run fully offline (yfinance is imported lazily and keyless). The shipped sample is **seeded, simulated** data, regenerable via `tools/gen_sample_data.py` and **labeled illustrative** (lab/data/sample/README.md) — never passed off as real history. The demo therefore runs reproducibly with the network off.
