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
