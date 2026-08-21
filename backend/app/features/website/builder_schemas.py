from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# Erlaubte Sektionstypen (fest laut Tech Design — kein freies CMS).
SectionTyp = Literal[
    "hero", "text_mit_bild", "leistungen", "kennzahlen",
    "ablauf", "faq", "kontakt", "cta",
]

# CTA-Ziele: nur diese drei, der Renderer bildet sie auf bestehende öffentliche
# Pfade/Anker ab. Damit existiert kein unprüfbarer Linkpfad.
CtaZiel = Literal["anfrage", "leistungen", "kontakt"]

# Sanfte Obergrenzen gegen ungebundene Speicherung (ponytail).
MAX_ITEMS = 50


# --- Inhalt je Typ (serverseitig geprüft, ohne HTML/CSS/JS) ---------------

class HeroInhalt(BaseModel):
    typ: Literal["hero"] = "hero"
    titel: str = ""
    text: str = ""
    cta_typ: CtaZiel = "anfrage"
    cta_text: str = ""


class TextMitBildInhalt(BaseModel):
    typ: Literal["text_mit_bild"] = "text_mit_bild"
    titel: str = ""
    text: str = ""


class LeistungenInhalt(BaseModel):
    typ: Literal["leistungen"] = "leistungen"
    titel: str = ""
    einleitung: str = ""
    cta_typ: CtaZiel = "leistungen"
    cta_text: str = ""


class KennzahlItem(BaseModel):
    wert: str = ""
    label: str = ""


class KennzahlenInhalt(BaseModel):
    typ: Literal["kennzahlen"] = "kennzahlen"
    titel: str = ""
    kennzahlen: list[KennzahlItem] = Field(default_factory=list, max_length=MAX_ITEMS)


class AblaufSchritt(BaseModel):
    titel: str = ""
    beschreibung: str = ""


class AblaufInhalt(BaseModel):
    typ: Literal["ablauf"] = "ablauf"
    titel: str = ""
    schritte: list[AblaufSchritt] = Field(default_factory=list, max_length=MAX_ITEMS)


class FaqItem(BaseModel):
    frage: str = ""
    antwort: str = ""


class FaqInhalt(BaseModel):
    typ: Literal["faq"] = "faq"
    titel: str = ""
    fragen: list[FaqItem] = Field(default_factory=list, max_length=MAX_ITEMS)


class KontaktInhalt(BaseModel):
    typ: Literal["kontakt"] = "kontakt"
    titel: str = ""
    einleitung: str = ""
    cta_typ: CtaZiel = "kontakt"
    cta_text: str = ""


class CtaInhalt(BaseModel):
    typ: Literal["cta"] = "cta"
    titel: str = ""
    text: str = ""
    cta_typ: CtaZiel = "anfrage"
    cta_text: str = ""


# Diskriminierte Union: das `typ`-Feld bestimmt die erlaubte Feldform.
SectionInhalt = Annotated[
    Union[
        HeroInhalt, TextMitBildInhalt, LeistungenInhalt, KennzahlenInhalt,
        AblaufInhalt, FaqInhalt, KontaktInhalt, CtaInhalt,
    ],
    Field(discriminator="typ"),
]


# --- Öffentliche Lesedaten (Renderer-Form) --------------------------------

class BildRef(BaseModel):
    url: str
    alt_text: str = ""


class PublicHeroInhalt(BaseModel):
    typ: Literal["hero"] = "hero"
    titel: str = ""
    text: str = ""
    cta_typ: CtaZiel = "anfrage"
    cta_text: str = ""
    bild: Optional[BildRef] = None


class PublicTextMitBildInhalt(BaseModel):
    typ: Literal["text_mit_bild"] = "text_mit_bild"
    titel: str = ""
    text: str = ""
    bild: Optional[BildRef] = None


class PublicLeistungenInhalt(BaseModel):
    typ: Literal["leistungen"] = "leistungen"
    titel: str = ""
    einleitung: str = ""
    cta_typ: CtaZiel = "leistungen"
    cta_text: str = ""


class PublicKennzahlenInhalt(BaseModel):
    typ: Literal["kennzahlen"] = "kennzahlen"
    titel: str = ""
    kennzahlen: list[KennzahlItem] = Field(default_factory=list, max_length=MAX_ITEMS)


class PublicAblaufInhalt(BaseModel):
    typ: Literal["ablauf"] = "ablauf"
    titel: str = ""
    schritte: list[AblaufSchritt] = Field(default_factory=list, max_length=MAX_ITEMS)


class PublicFaqInhalt(BaseModel):
    typ: Literal["faq"] = "faq"
    titel: str = ""
    fragen: list[FaqItem] = Field(default_factory=list, max_length=MAX_ITEMS)


class PublicKontaktInhalt(BaseModel):
    typ: Literal["kontakt"] = "kontakt"
    titel: str = ""
    einleitung: str = ""
    cta_typ: CtaZiel = "kontakt"
    cta_text: str = ""


class PublicCtaInhalt(BaseModel):
    typ: Literal["cta"] = "cta"
    titel: str = ""
    text: str = ""
    cta_typ: CtaZiel = "anfrage"
    cta_text: str = ""


PublicSectionInhalt = Annotated[
    Union[
        PublicHeroInhalt, PublicTextMitBildInhalt, PublicLeistungenInhalt,
        PublicKennzahlenInhalt, PublicAblaufInhalt, PublicFaqInhalt,
        PublicKontaktInhalt, PublicCtaInhalt,
    ],
    Field(discriminator="typ"),
]


# --- Builder-Lesedaten (Editor/Vorschau) ----------------------------------

class BildRead(BaseModel):
    url: str
    alt_text: str = ""


class BuilderSectionRead(BaseModel):
    id: str
    typ: SectionTyp
    visible: bool
    position: int
    inhalt: SectionInhalt
    bild: Optional[BildRead] = None


class BuilderStateRead(BaseModel):
    landingpage_id: str
    version: int
    sections: list[BuilderSectionRead]


# --- Schreib-Requests -----------------------------------------------------

class SectionAddRequest(BaseModel):
    # Request-Feld heißt `type` (wie im Tech Design spezifiziert), intern `typ`.
    type: SectionTyp = Field(alias="type")
    version: int

    model_config = ConfigDict(populate_by_name=True)


class SectionPatchRequest(BaseModel):
    version: int
    visible: Optional[bool] = None
    inhalt: SectionInhalt


class ReihenfolgeRequest(BaseModel):
    version: int
    ordered_ids: list[str] = Field(min_length=1)


class SectionVersionRequest(BaseModel):
    version: int
