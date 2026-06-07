"""View-layer smoke/integration tests.

Per PLAN.md we don't chase UI coverage (the UI is demonstrated by the
recording), but we do guard the M7 acceptance arc: build an iron condor and
see Greeks + payoff, run a backtest and watch costs eat in, and surface a
"sit-out" regime example.
"""
import pytest


@pytest.mark.django_db
def test_builder_renders_payoff_and_greeks(client):
    resp = client.get("/?preset=iron_condor&ticker=SPY")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Strategy Builder" in body
    assert "Net Greeks" in body
    assert "payoff-data" in body          # the embedded Plotly figure
    assert "Not financial advice." in body  # disclaimer present


@pytest.mark.django_db
def test_builder_htmx_returns_just_the_results_partial(client):
    resp = client.get("/?preset=straddle", HTTP_HX_REQUEST="true")
    body = resp.content.decode()
    assert resp.status_code == 200
    assert "payoff-data" in body
    assert "<html" not in body            # a fragment, not the full page


@pytest.mark.django_db
def test_builder_spike_scenario_says_sit_out(client):
    # THE judgment example: the regime that tells you not to trade.
    resp = client.get("/?preset=iron_condor&scenario=spike")
    assert "SIT OUT" in resp.content.decode()


@pytest.mark.django_db
def test_vol_page_renders_labeled_surface(client):
    resp = client.get("/vol")
    body = resp.content.decode()
    assert resp.status_code == 200
    assert "surface-data" in body
    assert "Illustrative" in body         # honesty: surface is labeled


@pytest.mark.django_db
def test_backtest_page_shows_cost_drag_and_metrics(client):
    resp = client.get("/backtest?ticker=SPY")
    body = resp.content.decode()
    assert resp.status_code == 200
    assert "Cost drag" in body            # costs visibly matter
    assert "with vs without" in body
    assert "equity-data" in body and "mc-data" in body


@pytest.mark.django_db
def test_unknown_ticker_falls_back_to_a_sample(client):
    resp = client.get("/?ticker=NONSENSE")
    assert resp.status_code == 200


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}
