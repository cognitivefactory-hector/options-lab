"""Plotly figure builders, themed for the terminal aesthetic.

Each function returns a JSON string (fig.to_json()) that the templates hand to
plotly.js (loaded from the CDN) via Plotly.newPlot. Keeping figure construction
in Python means the chart styling lives next to the data, server-side.
"""
import json

import numpy as np
import plotly.graph_objects as go

# Palette — kept in sync with the CSS design tokens in base.html.
INK = "#0a0e14"
TEXT = "#c9d3e0"
MUTED = "#6b7888"
GRID = "#1b2331"
AMBER = "#f0b429"
GREEN = "#3fb950"
RED = "#f85149"
CYAN = "#39c5cf"
FONT = "JetBrains Mono, ui-monospace, monospace"


def _layout(**over):
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=TEXT, size=12),
        margin=dict(l=56, r=20, t=30, b=44),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=MUTED, linecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.12, x=0),
        hovermode="x unified",
    )
    base.update(over)
    return base


def _json(fig):
    return fig.to_json()


def payoff_figure(spots, pnl, breakevens, spot):
    pnl = np.asarray(pnl)
    fig = go.Figure()
    # Profit/loss regions shaded against zero.
    fig.add_trace(go.Scatter(
        x=spots, y=np.where(pnl >= 0, pnl, 0), fill="tozeroy",
        line=dict(width=0), fillcolor="rgba(63,185,80,0.15)", hoverinfo="skip",
        showlegend=False))
    fig.add_trace(go.Scatter(
        x=spots, y=np.where(pnl < 0, pnl, 0), fill="tozeroy",
        line=dict(width=0), fillcolor="rgba(248,81,73,0.15)", hoverinfo="skip",
        showlegend=False))
    fig.add_trace(go.Scatter(
        x=spots, y=pnl, line=dict(color=AMBER, width=2.5), name="P&L at expiry"))
    fig.add_hline(y=0, line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_vline(x=spot, line=dict(color=CYAN, width=1, dash="dash"),
                  annotation_text="spot", annotation_font_color=CYAN)
    for be in breakevens:
        fig.add_vline(x=be, line=dict(color=TEXT, width=1, dash="dot"))
    fig.update_layout(_layout(xaxis_title="underlier at expiry", yaxis_title="net P&L ($)"))
    return _json(fig)


def iv_surface_figure(surface):
    fig = go.Figure(go.Surface(
        x=surface.strikes, y=surface.expiries, z=surface.iv,
        colorscale=[[0, INK], [0.5, "#8a6d1f"], [1, AMBER]],
        colorbar=dict(title="IV", outlinewidth=0)))
    fig.update_layout(_layout(
        scene=dict(
            xaxis=dict(title="strike", color=TEXT, gridcolor=GRID, backgroundcolor=INK),
            yaxis=dict(title="expiry (y)", color=TEXT, gridcolor=GRID, backgroundcolor=INK),
            zaxis=dict(title="implied vol", color=TEXT, gridcolor=GRID, backgroundcolor=INK),
        ),
        margin=dict(l=0, r=0, t=10, b=0),
    ))
    return _json(fig)


def skew_term_figure(surface):
    """2-D skew (mid expiry) + ATM term structure as a labeled fallback view."""
    mid = len(surface.expiries) // 2
    strikes, skew = surface.skew(surface.expiries[mid])
    expiries, term = surface.term_structure(surface.spot)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=skew, line=dict(color=AMBER, width=2.5),
                             name=f"skew @ {surface.expiries[mid]:.2f}y", yaxis="y"))
    fig.add_trace(go.Scatter(x=expiries, y=term, line=dict(color=CYAN, width=2.5),
                             name="ATM term structure", xaxis="x2", yaxis="y2"))
    fig.update_layout(_layout(
        grid=dict(rows=1, columns=2, pattern="independent"),
        xaxis=dict(title="strike", gridcolor=GRID),
        yaxis=dict(title="implied vol", gridcolor=GRID),
        xaxis2=dict(title="expiry (y)", gridcolor=GRID),
        yaxis2=dict(title="implied vol", gridcolor=GRID),
    ))
    return _json(fig)


def equity_figure(without_equity, with_equity):
    x = list(range(len(without_equity)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=without_equity, line=dict(color=MUTED, width=2, dash="dash"),
                             name="without costs"))
    fig.add_trace(go.Scatter(x=x, y=with_equity, line=dict(color=AMBER, width=2.5),
                             name="with costs"))
    fig.update_layout(_layout(xaxis_title="trade #", yaxis_title="equity ($)"))
    return _json(fig)


def montecarlo_fan_figure(paths):
    steps = paths.shape[1]
    x = list(range(steps))
    pct = {p: np.percentile(paths, p, axis=0) for p in (5, 25, 50, 75, 95)}
    fig = go.Figure()
    band = [(5, 95, "rgba(240,180,41,0.10)"), (25, 75, "rgba(240,180,41,0.20)")]
    for lo, hi, color in band:
        fig.add_trace(go.Scatter(x=x, y=pct[hi], line=dict(width=0), hoverinfo="skip",
                                 showlegend=False))
        fig.add_trace(go.Scatter(x=x, y=pct[lo], fill="tonexty", fillcolor=color,
                                 line=dict(width=0), name=f"{lo}–{hi} pct"))
    fig.add_trace(go.Scatter(x=x, y=pct[50], line=dict(color=AMBER, width=2.5), name="median"))
    fig.update_layout(_layout(xaxis_title="trading day", yaxis_title="simulated price ($)"))
    return _json(fig)


def to_plot_payload(*figures_json):
    """Bundle named figure JSON for a single template variable."""
    return json.dumps({name: json.loads(fig) for name, fig in figures_json})
