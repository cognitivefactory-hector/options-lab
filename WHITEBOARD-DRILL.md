# Whiteboard Drill — Options Lab (design-stage)

> Rehearsal for the recorded whiteboard session. **The push** is me playing tough reviewer; **Defense** is the position that survives; **⚠ Your move** is what only you can answer once you've built/measured it. Fold the survivors into `DECISIONS.md`, then record.
> Scope: design-stage. Re-run after **M4** (backtest + costs) with real with/without-costs numbers in hand.

## Q1 — "Every backtest looks great in hindsight. Prove it isn't curve-fit or data-snooped."
**The push:** You tuned until the curve looked good.
**Defense (survives):** Walk-forward only — rolling in-sample → out-of-sample, never a single in-sample fit. Scaler fit on train, the forecast origin is fixed, no row shuffling. I also Monte-Carlo the *outcome distribution* rather than reporting one lucky path, and I check parameter stability across folds. If a result only survives one parameter set, I treat it as overfit.
**⚠ Your move:** Show the out-of-sample vs. in-sample gap and a parameter-stability plot — the proof, not the claim.

## Q2 — "You're using free, delayed data with thin options chains. Garbage in, garbage out."
**The push:** Your inputs are junk, so your conclusions are junk.
**Defense (survives):** I separate what I *compute* from what I *trust*. Greeks/payoffs come from Black-Scholes on the underlier (sound); where real historical chains aren't available I **reconstruct option prices from the underlier + a vol assumption and label it a model approximation.** I'm explicit that this proves method, not a live edge. Knowing the difference is the competence.
**⚠ Your move:** State exactly which results depend on the BS reconstruction vs. real data.

## Q3 — "Stock prices are ~a random walk. Forecasting them is a fool's errand."
**The push:** The whole financial premise is bankrupt.
**Defense (survives):** Agreed on price *level* — so I don't bet on it. What's more forecastable is **volatility / regime**, and the tool's job is the *decision process* (when the regime favors a structure, how to size), not a price oracle. The honest framing is the point: I'm demonstrating method and risk discipline, not claiming to beat the market.

## Q4 — "Where are transaction costs, slippage, bid/ask, assignment? Retail backtests die live without them."
**The push:** Your returns are a fantasy.
**Defense (survives):** There's an explicit cost model — commission, slippage, spread, assignment — with a **with/without-costs toggle**, and a test that enforces costs always reduce net return. I *want* to see the alpha shrink under costs; a strategy that only works frictionless isn't a strategy.
**⚠ Your move:** Have the with-vs-without-costs delta on a real run ready to show.

## Q5 — "Your regime filter is just another knob you tuned to make the curve nicer."
**The push:** You fit the filter after seeing the results.
**Defense (survives):** The filter is defined **a priori** from volatility logic (realized-vol percentile / term structure) — set before fitting, not optimized to flatter the backtest. Its most important output is **"sit out,"** which a curve-fitter would never add because it *reduces* trade count.
**⚠ Your move:** Show the filter rule was specified before the backtest (commit history helps).

## Q6 — "Show me the trade you DIDN'T take. Anyone can show winners."
**The push:** Where's the judgment?
**Defense (survives):** The headline artifact is a regime where the tool says **sit out** and I didn't put the trade on — plus a position I sized *down* to survive a tail rather than maximize growth. Sizing to risk, not conviction, and being able to point at the declined trade, is the whole signal.
**⚠ Your move:** Capture one concrete "regime said sit out" example from a real run to narrate.

## Verdict — SDRC after the drill
- **Holds:** robustness-over-return; the declined-trade thesis; growth-for-survivability trade.
- **Sharpen:** label exactly what rests on the BS price reconstruction (Q2); prove the regime filter is a-priori (Q5); have the cost delta + the sit-out example ready (Q4, Q6).
- **Land this line in the room:** *"The valuable output isn't the green curve — it's knowing when there's no edge, and sizing so one tail event doesn't end me."*

---

## Recording day — concrete numbers + a 6-minute script

All figures below are from the shipped (seeded, **simulated**) sample, reproducible via the app or `pytest`. They prove method, not a live edge — say so on camera.

**Numbers to have on screen:**
- **Sit-out:** Builder → *Volatility spike* scenario → **SIT OUT** (realized vol 0.98, vol percentile 0.98, **term ratio 1.60**). Live SPY for contrast → **NEUTRAL** (rv 0.09, pct 0.04, term 0.76).
- **Costs:** Backtest → short ATM straddle, 23 trades → ends lower **with** costs than without, every time (test-enforced).
- **The honest loser:** that backtest is **CAGR ≈ −7%, Sharpe ≈ −1.4** on SPY — show it, don't hide it.
- **Sizing:** $100k / 2% / $500 worst case → **4 contracts, $2k at risk**; Kelly capped, never full.

**Script (≈6 min):**
1. **(0:00) Thesis.** "Anyone can show a green curve. I'll show you the trade I *didn't* take." (SDRC Situation → Decision.)
2. **(0:45) Builder.** Build the iron condor; point at payoff, net Greeks, breakevens, P(profit). Premiums are BS-derived so it's internally consistent.
3. **(2:00) The sit-out.** Flip to the *vol spike* scenario → **SIT OUT**. Tie it to the a-priori rule (term ratio > 1.20). "A curve-fitter never adds an output that cuts trade count."
4. **(3:15) Costs.** Backtest with vs without costs; name the drag; "a strategy that only works frictionless isn't a strategy."
5. **(4:15) The honest loser + robustness.** "This short-straddle is a *loser* here — no edge in this regime. Walk-forward, not a single in-sample fit; Monte-Carlo the distribution, not one path."
6. **(5:15) Risk.** Sizing to survive a tail (capped Kelly, never full); the growth-for-survivability trade I *accept*. Close on the line above.

**Pre-record checklist:**
- [ ] App running (live demo URL or `make run`); Builder/Vol/Backtest loaded in tabs.
- [ ] Screen + mic test (Loom or OBS → MP4), 5–8 min.
- [ ] Walk the **declined-trade** example explicitly (challenge #5/#6).
- [ ] Concede at least one fair point under push-back (or give a crisp reason you hold).
- [ ] After: fold surviving reasoning into `DECISIONS.md`; paste the recording link into `DECISIONS.md` + `README.md` + hector-garza.com.
