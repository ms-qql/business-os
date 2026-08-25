from __future__ import annotations

import datetime
import uuid
from typing import Optional

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return value
    if isinstance(value, str):
        return datetime.date.fromisoformat(value[:10])
    return value


def get_einstellung(mandant_id: str) -> Optional[dict]:
    rows = db.engine.query(
        "SELECT id, mandant_id, leistungs_formular_id, leistungs_feld_id, "
        "wunschtermin_feld_id, naechster_freier_termin, created_at, updated_at "
        "FROM triage_einstellung WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    if not rows:
        return None
    r = dict(rows[0])
    r["naechster_freier_termin"] = _to_date(r.get("naechster_freier_termin"))
    return r


def get_werte(mandant_id: str, einstellung_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT wert, klassifikation FROM triage_leistungswert "
        "WHERE mandant_id = %s AND einstellung_id = %s ORDER BY wert",
        (mandant_id, einstellung_id), mandant_id=mandant_id,
    )


def replace_einstellung(mandant_id: str, formular_id: str, feld_id: str,
                        wunschtermin_feld_id: Optional[str],
                        werte: list[dict]) -> dict:
    """Atomarer Vollersatz: Formular/Feld-Bezüge + komplette Werteliste."""
    with db.engine.transaction(mandant_id=mandant_id) as ctx:
        row = get_einstellung(mandant_id)
        if row:
            eid = row["id"]
            ctx.command(
                "UPDATE triage_einstellung SET leistungs_formular_id = %s, "
                "leistungs_feld_id = %s, wunschtermin_feld_id = %s, updated_at = %s "
                "WHERE mandant_id = %s",
                (formular_id, feld_id, wunschtermin_feld_id, _now(), mandant_id),
            )
        else:
            eid = str(uuid.uuid4())
            ctx.command(
                "INSERT INTO triage_einstellung (id, mandant_id, leistungs_formular_id, "
                "leistungs_feld_id, wunschtermin_feld_id) VALUES (%s, %s, %s, %s, %s)",
                (eid, mandant_id, formular_id, feld_id, wunschtermin_feld_id),
            )
        ctx.command(
            "DELETE FROM triage_leistungswert WHERE mandant_id = %s AND einstellung_id = %s",
            (mandant_id, eid),
        )
        for w in werte:
            ctx.command(
                "INSERT INTO triage_leistungswert (id, mandant_id, einstellung_id, "
                "wert, klassifikation) VALUES (%s, %s, %s, %s, %s)",
                (str(uuid.uuid4()), mandant_id, eid, w["wert"], w["klassifikation"]),
            )
    return get_einstellung(mandant_id)


def set_kapazitaet(mandant_id: str, datum: Optional[datetime.date]) -> dict:
    row = get_einstellung(mandant_id)
    if row:
        db.engine.command(
            "UPDATE triage_einstellung SET naechster_freier_termin = %s, updated_at = %s "
            "WHERE mandant_id = %s",
            (datum, _now(), mandant_id), mandant_id=mandant_id,
        )
    else:
        db.engine.command(
            "INSERT INTO triage_einstellung (id, mandant_id, naechster_freier_termin) "
            "VALUES (%s, %s, %s)",
            (str(uuid.uuid4()), mandant_id, datum), mandant_id=mandant_id,
        )
    return get_einstellung(mandant_id)
