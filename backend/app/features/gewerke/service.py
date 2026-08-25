from __future__ import annotations

from decimal import Decimal

from app.errors import ConflictError, NotFoundError, ValidationError
from app.features.gewerke import repository as repo
from app.features.gewerke import schemas
from app.features.angebote import repository as angebote_repo
from app.features.angebote import service as angebote_service
from app.features.angebote import schemas as angebote_schemas


# --- Berechnungsregeln (Tech Design Abschnitt Rechen- und Snapshot-Regeln) -


def _vk_zeile(z: schemas.KostenzeileBase) -> float:
    """VK je Kostenzeile auf 2 Dezimalstellen: VK = Menge × (EK + (EK × Zuschlag/100))."""
    einzel = z.ek_einzelpreis + (z.ek_einzelpreis * z.zuschlag_prozent / 100)
    vk = z.menge * einzel
    return round(vk, 2)


def gewerk_vk_preis(zeilen: list) -> float:
    """Summe der Zeilen-VKs (gerundet)."""
    total = 0.0
    for z in zeilen:
        if isinstance(z, schemas.KostenzeileBase):
            total += _vk_zeile(z)
        else:
            # dict aus der Repository (Decimal-Werte aus NUMERIC).
            ek = float(z["ek_einzelpreis"])
            zuschlag = float(z["zuschlag_prozent"])
            menge = float(z["menge"])
            total += round(menge * (ek + (ek * zuschlag / 100)), 2)
    return round(total, 2)


def _zeile_read(z: dict) -> schemas.KostenzeileRead:
    return schemas.KostenzeileRead(
        id=z["id"], gewerk_id=z["gewerk_id"], kostenart=z["kostenart"],
        menge=float(z["menge"]), einheit=z["einheit"],
        ek_einzelpreis=float(z["ek_einzelpreis"]),
        zuschlag_prozent=float(z["zuschlag_prozent"]),
        vk_preis=_vk_zeile(schemas.KostenzeileBase(
            kostenart=z["kostenart"], menge=float(z["menge"]), einheit=z["einheit"],
            ek_einzelpreis=float(z["ek_einzelpreis"]),
            zuschlag_prozent=float(z["zuschlag_prozent"]),
        )),
    )


def _gewerk_read(g: dict, zeilen: list) -> schemas.GewerkRead:
    return schemas.GewerkRead(
        id=g["id"], bezeichnung=g["bezeichnung"], einheit=g["einheit"],
        kalkulationsart=g["kalkulationsart"], kategorie_id=g.get("kategorie_id"),
        langbeschreibung=g.get("langbeschreibung"),
        steuersatz=float(g["steuersatz"]),
        kostenzeilen=[_zeile_read(z) for z in zeilen],
        vk_preis=gewerk_vk_preis(zeilen),
    )


# --- Kategorien ----------------------------------------------------------

def list_kategorien(user) -> list[schemas.KategorieRead]:
    return [schemas.KategorieRead(**k) for k in repo.list_kategorien(user.mandant_id)]


def create_kategorie(user, payload: schemas.KategorieCreate) -> schemas.KategorieRead:
    name = payload.name.strip()
    if not name:
        raise ValidationError("Der Kategoriename darf nicht leer sein.")
    if repo.find_kategorie_by_name(user.mandant_id, name):
        raise ConflictError(f"Die Kategorie „{name}“ existiert bereits.")
    return schemas.KategorieRead(**repo.create_kategorie(user.mandant_id, name))


def rename_kategorie(user, kategorie_id: str, payload: schemas.KategorieCreate) -> schemas.KategorieRead:
    existing = repo.get_kategorie(user.mandant_id, kategorie_id)
    if not existing:
        raise NotFoundError("Kategorie nicht gefunden.")
    name = payload.name.strip()
    if not name:
        raise ValidationError("Der Kategoriename darf nicht leer sein.")
    return schemas.KategorieRead(**repo.rename_kategorie(user.mandant_id, kategorie_id, name))


def delete_kategorie(user, kategorie_id: str) -> None:
    existing = repo.get_kategorie(user.mandant_id, kategorie_id)
    if not existing:
        raise NotFoundError("Kategorie nicht gefunden.")
    repo.delete_kategorie(user.mandant_id, kategorie_id)


# --- Gewerke -------------------------------------------------------------

def list_gewerke(user, suchbegriff: str | None, kategorie_id: str | None) -> schemas.GewerkListe:
    items = []
    for g in repo.list_gewerke(user.mandant_id, suchbegriff, kategorie_id):
        zeilen = repo.list_kostenzeilen(user.mandant_id, g["id"])
        items.append(schemas.GewerkListeItem(
            id=g["id"], bezeichnung=g["bezeichnung"], einheit=g["einheit"],
            kalkulationsart=g["kalkulationsart"], kategorie_id=g.get("kategorie_id"),
            vk_preis=gewerk_vk_preis(zeilen),
        ))
    return schemas.GewerkListe(items=items)


def get_gewerk(user, gewerk_id: str) -> schemas.GewerkRead:
    g = repo.get_gewerk(user.mandant_id, gewerk_id)
    if not g:
        raise NotFoundError("Gewerk nicht gefunden.")
    zeilen = repo.list_kostenzeilen(user.mandant_id, g["id"])
    return _gewerk_read(g, zeilen)


def _validate_kostenzeilen(zeilen: list[schemas.KostenzeileBase]) -> None:
    if not zeilen:
        raise ValidationError("Mindestens eine Kostenzeile ist erforderlich.")
    seen = set()
    for z in zeilen:
        if (z.kostenart, z.einheit, round(z.ek_einzelpreis, 2), round(z.zuschlag_prozent, 2)) in seen:
            raise ValidationError("Doppelte Kostenzeilen sind nicht erlaubt.")
        seen.add((z.kostenart, z.einheit, round(z.ek_einzelpreis, 2),
                  round(z.zuschlag_prozent, 2)))


def _check_duplikat(user, bezeichnung: str, einheit: str, gewerk_id: str | None) -> None:
    """Gleiche Bezeichnung + Einheit -> bestätigungspflichtige Warnung,
    außer bei explizitem duplikat_bestaetigt (nicht beim Patch identischer Werte)."""
    if gewerk_id:
        current = repo.get_gewerk(user.mandant_id, gewerk_id)
        if current and current["bezeichnung"] == bezeichnung and current["einheit"] == einheit:
            return  # unveränderte Identität -> kein Konflikt
    existing = repo.find_gewerk_by_bezeichnung_einheit(user.mandant_id, bezeichnung, einheit)
    if existing and existing["id"] != gewerk_id:
        raise ConflictError(
            "Es existiert bereits ein Gewerk mit derselben Bezeichnung und Einheit. "
            "Zum Speichern bitte bestätigen.",
        )


def create_gewerk(user, payload: schemas.GewerkCreate) -> schemas.GewerkRead:
    bezeichnung = payload.bezeichnung.strip()
    einheit = payload.einheit.strip()
    if not bezeichnung or not einheit:
        raise ValidationError("Bezeichnung und Einheit sind erforderlich.")
    _validate_kostenzeilen(payload.kostenzeilen)
    duplikat = repo.find_gewerk_by_bezeichnung_einheit(user.mandant_id, bezeichnung, einheit)
    if duplikat and not payload.duplikat_bestaetigt:
        raise ConflictError(
            "Es existiert bereits ein Gewerk mit derselben Bezeichnung und Einheit. "
            "Zum Speichern bitte bestätigen.",
        )
    g = repo.create_gewerk(
        user.mandant_id, kategorie_id=payload.kategorie_id, bezeichnung=bezeichnung,
        langbeschreibung=payload.langbeschreibung, einheit=einheit,
        kalkulationsart=payload.kalkulationsart, steuersatz=payload.steuersatz,
    )
    zeilen = repo.replace_kostenzeilen(
        user.mandant_id, g["id"],
        [z.model_dump() for z in payload.kostenzeilen],
    )
    return _gewerk_read(g, zeilen)


def update_gewerk(user, gewerk_id: str, payload: schemas.GewerkUpdate) -> schemas.GewerkRead:
    g = repo.get_gewerk(user.mandant_id, gewerk_id)
    if not g:
        raise NotFoundError("Gewerk nicht gefunden.")
    updates: dict = {}
    if payload.bezeichnung is not None:
        updates["bezeichnung"] = payload.bezeichnung.strip()
    if payload.einheit is not None:
        updates["einheit"] = payload.einheit.strip()
    if payload.kalkulationsart is not None:
        updates["kalkulationsart"] = payload.kalkulationsart
    if "kategorie_id" in payload.model_fields_set:
        updates["kategorie_id"] = payload.kategorie_id
    if "langbeschreibung" in payload.model_fields_set:
        updates["langbeschreibung"] = payload.langbeschreibung
    if payload.steuersatz is not None:
        updates["steuersatz"] = payload.steuersatz

    neue_bez = updates.get("bezeichnung", g["bezeichnung"])
    neue_einheit = updates.get("einheit", g["einheit"])
    if (neue_bez != g["bezeichnung"] or neue_einheit != g["einheit"]) and not payload.duplikat_bestaetigt:
        duplikat = repo.find_gewerk_by_bezeichnung_einheit(
            user.mandant_id, neue_bez, neue_einheit)
        if duplikat and duplikat["id"] != gewerk_id:
            raise ConflictError(
                "Es existiert bereits ein Gewerk mit derselben Bezeichnung und Einheit. "
                "Zum Speichern bitte bestätigen.",
            )

    if updates:
        g = repo.update_gewerk(user.mandant_id, gewerk_id, updates)

    if payload.kostenzeilen is not None:
        _validate_kostenzeilen(payload.kostenzeilen)
        repo.replace_kostenzeilen(
            user.mandant_id, gewerk_id,
            [z.model_dump() for z in payload.kostenzeilen],
        )

    zeilen = repo.list_kostenzeilen(user.mandant_id, gewerk_id)
    return _gewerk_read(g, zeilen)


def delete_gewerk(user, gewerk_id: str) -> None:
    g = repo.get_gewerk(user.mandant_id, gewerk_id)
    if not g:
        raise NotFoundError("Gewerk nicht gefunden.")
    repo.delete_gewerk(user.mandant_id, gewerk_id)


# --- Angebot-Position aus Gewerk (Snapshot, keine Live-Referenz) ----------

def add_position_aus_gewerk(user, angebot_id: str, payload) -> dict:
    angebot = angebote_repo.get_angebot(user.mandant_id, angebot_id)
    if not angebot:
        raise NotFoundError("Angebot nicht gefunden.")
    if angebot["status"] != "entwurf":
        raise ConflictError(
            "Ein versendetes Angebot kann nicht mehr geändert werden — erstellen Sie eine neue Version.",
        )
    if payload.menge <= 0:
        raise ValidationError("Die Menge muss größer als 0 sein.")
    g = repo.get_gewerk(user.mandant_id, payload.gewerk_id)
    if not g:
        raise NotFoundError("Gewerk nicht gefunden.")

    zeilen = repo.list_kostenzeilen(user.mandant_id, g["id"])
    vk = gewerk_vk_preis(zeilen)
    # Bei gesamtpreis: Position mit Menge 1, VK ist Einzel- und Gesamtpreis.
    menge = 1.0 if g["kalkulationsart"] == "gesamtpreis" else float(payload.menge)
    einzelpreis = round(vk, 2)

    pos = repo.create_position_aus_gewerk(
        user.mandant_id, angebot_id, bezeichnung=g["bezeichnung"],
        einheit=g["einheit"], steuersatz=float(g["steuersatz"]), menge=menge,
        einzelpreis=einzelpreis, kalkulierter_einzelpreis=einzelpreis,
        sortierung=payload.sortierung,
    )
    angebote_service._recalc_and_store(user.mandant_id, angebot_id)
    from app.features.vorgaenge import repository as vorgaenge_repo

    vorgaenge_repo.add_historie(
        user.mandant_id, angebot["vorgang_id"], "angebot_position_hinzugefuegt",
        g["bezeichnung"], user.id)
    return angebote_service._detail(user.mandant_id, angebot_id)


def override_position_preis(user, angebot_id: str, position_id: str, payload) -> dict:
    """Setzt den tatsächlichen Einzelpreis einer kalkulierten Position. Bei
    Abweichung vom kalkulierten Wert ist eine interne Begründung Pflicht; wird
    exakt auf den kalkulierten Wert zurückgestellt, werden beide Felder geleert."""
    angebot = angebote_repo.get_angebot(user.mandant_id, angebot_id)
    if not angebot:
        raise NotFoundError("Angebot nicht gefunden.")
    if angebot["status"] != "entwurf":
        raise ConflictError(
            "Ein versendetes Angebot kann nicht mehr geändert werden — erstellen Sie eine neue Version.",
        )
    pos = repo.get_position(user.mandant_id, angebot_id, position_id)
    if not pos:
        raise NotFoundError("Position nicht gefunden.")
    if pos.get("kalkulierter_einzelpreis") is None:
        # Manuelle Position: kein Override-Nachweis, einfache Preisänderung.
        return angebote_service.update_position(
            user, angebot_id, position_id,
            angebote_schemas.PositionUpdate(einzelpreis=payload.einzelpreis))

    kalkuliert = float(pos["kalkulierter_einzelpreis"])
    neu = float(payload.einzelpreis)
    if abs(neu - kalkuliert) < 0.005:
        # Auf kalkulierten Wert zurückgestellt -> Override-Felder leeren.
        repo.update_position_override(
            user.mandant_id, angebot_id, position_id,
            {"einzelpreis": kalkuliert, "preis_override_begruendung": None})
    else:
        if not (payload.begruendung and payload.begruendung.strip()):
            raise ValidationError(
                "Bei einer Abweichung vom kalkulierten Preis ist eine interne Begründung erforderlich.")
        repo.update_position_override(
            user.mandant_id, angebot_id, position_id,
            {"einzelpreis": neu,
             "preis_override_begruendung": payload.begruendung.strip()})
    angebote_service._recalc_and_store(user.mandant_id, angebot_id)
    return angebote_service._detail(user.mandant_id, angebot_id)
