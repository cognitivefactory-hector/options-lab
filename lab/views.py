"""Django views — thin layer over the framework-free studio/quant modules.

Each view loads sample (or cached) bars, calls `lab.studio` to compute, builds
Plotly figures with `lab.charts`, and renders a template. No quant logic lives
here; the views just marshal request params and pass results to templates.
"""
from django.http import JsonResponse
from django.shortcuts import render

from lab import charts, studio
from lab.data.fetch import SAMPLE_TICKERS, closes, load_sample
from lab.regime.vol_regime import FAVORABLE, NEUTRAL, SIT_OUT

REGIME_COPY = {
    FAVORABLE: ("FAVORABLE", "Premium is rich and vol isn't spiking — a defensible window "
                             "for short premium."),
    NEUTRAL: ("NEUTRAL", "No clear edge. The honest output is often to wait."),
    SIT_OUT: ("SIT OUT", "Vol is spiking / backwardated — exactly where short premium gets "
                         "run over. The trade you don't put on."),
}


def _f(request, key, default):
    try:
        return float(request.GET.get(key, default))
    except (TypeError, ValueError):
        return default


def _ticker(request):
    t = request.GET.get("ticker", SAMPLE_TICKERS[0])
    return t if t in SAMPLE_TICKERS else SAMPLE_TICKERS[0]


def _builder_context(request):
    preset = request.GET.get("preset", "iron_condor")
    if preset not in studio.PRESETS:
        preset = "iron_condor"
    ticker = _ticker(request)
    sigma = _f(request, "sigma", 0.20)
    r = _f(request, "r", 0.04)
    dte = _f(request, "dte", 0.25)
    scenario = request.GET.get("scenario", "live")

    bars = load_sample(ticker)
    underlier = closes(bars)
    spot = round(float(underlier[-1]), 2)

    position = studio.build_position(preset, spot, sigma, r, dte)
    summary = studio.position_summary(position, spot, sigma, r, dte)
    spots, pnl = studio.payoff_series(position, spot)
    payoff_json = charts.payoff_figure(spots, pnl, summary["breakevens"], spot)

    verdict, read = studio.regime_for(studio.scenario_closes(scenario, underlier))
    verdict_label, verdict_note = REGIME_COPY[verdict]

    return {
        "presets": studio.PRESETS,
        "preset": preset,
        "tickers": SAMPLE_TICKERS,
        "ticker": ticker,
        "sigma": sigma, "r": r, "dte": dte, "spot": spot,
        "scenario": scenario,
        "summary": summary,
        "payoff_json": payoff_json,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_note": verdict_note,
        "regime": {"realized_vol": round(read.realized_vol, 3),
                   "vol_percentile": round(read.vol_percentile, 2),
                   "term_ratio": round(read.term_ratio, 2)},
    }


def builder(request):
    ctx = _builder_context(request)
    is_htmx = request.headers.get("HX-Request")
    template = "lab/_builder_results.html" if is_htmx else "lab/builder.html"
    return render(request, template, ctx)


def vol(request):
    ticker = _ticker(request)
    bars = load_sample(ticker)
    spot = round(float(closes(bars)[-1]), 2)
    r = _f(request, "r", 0.04)
    surface = studio.illustrative_surface(spot, r)
    ctx = {
        "tickers": SAMPLE_TICKERS, "ticker": ticker, "spot": spot,
        "surface_json": charts.iv_surface_figure(surface),
        "skew_json": charts.skew_term_figure(surface),
    }
    return render(request, "lab/vol.html", ctx)


def backtest(request):
    ticker = _ticker(request)
    bars = load_sample(ticker)
    underlier = closes(bars)
    spot = round(float(underlier[-1]), 2)
    _, read = studio.regime_for(underlier)
    sigma = max(round(read.realized_vol, 3), 0.05)

    without, with_costs = studio.backtest_demo(underlier, sigma=sigma)
    paths = studio.montecarlo_demo(spot, mu=0.05, sigma=sigma)

    cost_gap = round(without.equity[-1] - with_costs.equity[-1], 2)
    ctx = {
        "tickers": SAMPLE_TICKERS, "ticker": ticker, "sigma": sigma,
        "n_trades": with_costs.n_trades,
        "cost_gap": cost_gap,
        "metrics_without": without.metrics._asdict(),
        "metrics_with": with_costs.metrics._asdict(),
        "equity_json": charts.equity_figure(without.equity, with_costs.equity),
        "mc_json": charts.montecarlo_fan_figure(paths),
    }
    return render(request, "lab/backtest.html", ctx)


def healthz(request):
    return JsonResponse({"status": "ok"})
