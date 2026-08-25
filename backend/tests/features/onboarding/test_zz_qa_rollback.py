"""QA: Verifiziert Atomaritaet (ADR-14-3) bei Fehler mitten in der Uebernahme."""
import pytest
from unittest.mock import patch

from conftest import make_user

from app import db


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def test_rollback_on_partial_failure(client, mandant):
    """Schlaegt die Formular-Kopie (Schritt 3) fehl, duerfen weder Leistungsseiten
    noch Preisliste noch die Paketkennung uebrig bleiben (kein Teilbestand)."""
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    from app.features.formulare import repository as formular_repo

    with patch.object(formular_repo, "seed_template_tx", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            client.post("/onboarding/branchenpaket-uebernehmen",
                        headers={"Authorization": f"Bearer {tok}"},
                        json={"kennung": "shk"})

    leist = db.engine.query("SELECT COUNT(*) AS c FROM leistungsseite WHERE mandant_id = %s",
                            (mandant,), mandant_id=mandant)
    assert int(leist[0]["c"]) == 0, "Rollback fehlgeschlagen: Leistungsseiten blieben nach Fehler bestehen"
    gewerk = db.engine.query("SELECT COUNT(*) AS c FROM gewerk WHERE mandant_id = %s",
                            (mandant,), mandant_id=mandant)
    assert int(gewerk[0]["c"]) == 0, "Rollback fehlgeschlagen: Gewerke blieben nach Fehler bestehen"
    rows = db.engine.query("SELECT branchenpaket_kennung FROM mandanten WHERE id = %s",
                           (mandant,), mandant_id=mandant)
    assert rows[0]["branchenpaket_kennung"] is None, "Rollback fehlgeschlagen: Paketkennung wurde trotz Fehler gesetzt"

    # Danach muss eine erneute (korrekte) Uebernahme moeglich sein (kein Teilbestand blockiert 409).
    r2 = client.post("/onboarding/branchenpaket-uebernehmen",
                     headers={"Authorization": f"Bearer {tok}"},
                     json={"kennung": "shk"})
    assert r2.status_code == 201, r2.text
