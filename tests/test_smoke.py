"""M0 smoke tests — the app serves and the disclaimer is present.

The quant core (pricing/Greeks/IV/backtest) is tested hard and test-first from
M1 onward; this file only guards the scaffold.
"""
import pytest


@pytest.mark.django_db
def test_index_serves_with_disclaimer(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Not financial advice." in response.content


def test_healthz_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
