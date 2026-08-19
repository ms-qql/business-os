from __future__ import annotations

import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def _de(value: float) -> str:
    """Deutsches Dezimalformat, zwei Nachkommastellen (z. B. '1.234,50')."""
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def render_rechnung_pdf(*, rechnungsnummer: str, rechnungsdatum: str,
                        leistungsdatum: str, betrieb_name: str,
                        rechnungssteller: dict, kunde: dict, objekt: dict,
                        positionen: list[dict], netto_summe: float,
                        steuer_summe: float, brutto_summe: float,
                        storniert: bool = False) -> bytes:
    """Rendert das Rechnungs-HTML-Template zu PDF-Bytes. Läuft ausschließlich auf
    serverseitig gespeicherten Daten (nie aus Client-HTML), siehe Tech Design ADR-8-2."""
    from xhtml2pdf import pisa

    positionen_txt = [
        {
            **p,
            "einzelpreis_txt": _de(p["netto_einzelpreis"]),
            "positions_summe_txt": _de(p["positions_summe"]),
        }
        for p in positionen
    ]
    template = _env.get_template("rechnung_pdf.html")
    html = template.render(
        rechnungsnummer=rechnungsnummer, rechnungsdatum=rechnungsdatum,
        leistungsdatum=leistungsdatum, betrieb_name=betrieb_name,
        rechnungssteller=rechnungssteller, kunde=kunde, objekt=objekt,
        positionen=positionen_txt, netto_txt=_de(netto_summe),
        steuer_txt=_de(steuer_summe), brutto_txt=_de(brutto_summe),
        kopf={"storniert": storniert},
    )
    buffer = io.BytesIO()
    result = pisa.CreatePDF(io.StringIO(html), dest=buffer)
    if result.err:
        raise RuntimeError("PDF-Erzeugung fehlgeschlagen.")
    return buffer.getvalue()
