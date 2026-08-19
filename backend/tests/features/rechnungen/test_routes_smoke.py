from fastapi.testclient import TestClient
from app.main import app


def test_rechnungen_routes_registered():
    c = TestClient(app)
    spec = c.get("/openapi.json").json()
    paths = spec["paths"].keys()
    for p in ("/einstellungen/rechnungssteller", "/vorgaenge/{vorgang_id}/rechnungen",
              "/rechnungen/{rechnung_id}/freigabe", "/rechnungen/{rechnung_id}/senden",
              "/rechnungen/{rechnung_id}/storno", "/rechnungen/{rechnung_id}/zahlungsstatus",
              "/rechnungen/{rechnung_id}/pdf", "/rechnungen/{rechnung_id}/positionen"):
        assert p in paths, f"fehlender Pfad: {p}"


def test_health_still_ok():
    c = TestClient(app)
    assert c.get("/health").status_code == 200
