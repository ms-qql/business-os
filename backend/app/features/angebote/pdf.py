from __future__ import annotations

import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def _de(value: float) -> str:
    """Deutsches Dezimalformat, zwei Nachkommastellen (z. B. '1.234,50')."""
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _rabatt_txt(rabatt_typ: str, rabatt_wert: float) -> str:
    if rabatt_typ == "prozent":
        return f"{_de(rabatt_wert)} %"
    return f"{_de(rabatt_wert)} €"


def render_angebot_pdf(*, angebot_nummer: str, version: int, gueltig_bis: str | None,
                       betrieb_name: str, kunde_name: str, kunde_email: str | None,
                       kunde_telefon: str | None, positionen: list[dict], netto_summe: float,
                       steuer_summe: float, brutto_summe: float, freitext: str | None) -> bytes:
    """Rendert das Angebots-HTML-Template zu PDF-Bytes. Läuft ausschließlich auf
    serverseitig gespeicherten Daten (nie aus Client-HTML), siehe Tech Design."""
    from xhtml2pdf import pisa

    positionen_txt = [
        {
            **p,
            "einzelpreis_txt": _de(p["einzelpreis"]),
            "positions_summe_txt": _de(p["positions_summe"]),
            "rabatt_txt": _rabatt_txt(p["rabatt_typ"], p["rabatt_wert"]),
        }
        for p in positionen
    ]
    template = _env.get_template("angebot_pdf.html")
    html = template.render(
        angebot_nummer=angebot_nummer, version=version, gueltig_bis=gueltig_bis,
        betrieb_name=betrieb_name, kunde_name=kunde_name, kunde_email=kunde_email,
        kunde_telefon=kunde_telefon, positionen=positionen_txt, netto_txt=_de(netto_summe),
        steuer_txt=_de(steuer_summe), brutto_txt=_de(brutto_summe), freitext=freitext,
    )
    buffer = io.BytesIO()
    result = pisa.CreatePDF(io.StringIO(html), dest=buffer)
    if result.err:
        raise RuntimeError("PDF-Erzeugung fehlgeschlagen.")
    return buffer.getvalue()
