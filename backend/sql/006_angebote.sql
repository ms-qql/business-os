-- PROJ-5: Angebote, PDF, Freigabe und Versand.
-- Gleiches Muster wie 003_kunden_vorgaenge.sql: jede Fachtabelle trägt
-- mandant_id und ist per RLS auf current_setting('app.current_mandant_id')
-- begrenzt. Das erzeugte PDF selbst liegt weiterhin in vorgang_dokument/MinIO
-- (angebot.dokument_id verweist darauf) — kein zweiter Dateispeicherpfad.

-- Zähler pro Mandant für lückenlose, mandantengetrennte Angebotsnummern.
-- Wird transaktional per SELECT ... FOR UPDATE hochgezählt (siehe
-- app/features/angebote/repository.py::next_angebot_nummer).
CREATE TABLE IF NOT EXISTS angebot_nummernkreis (
    mandant_id UUID PRIMARY KEY REFERENCES mandanten(id) ON DELETE CASCADE,
    letzte_nummer INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS angebot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    vorgang_id UUID NOT NULL REFERENCES vorgang(id) ON DELETE CASCADE,
    angebot_nummer TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    vorgaenger_angebot_id UUID REFERENCES angebot(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf', 'versendet')),
    gueltig_bis DATE,
    freitext TEXT,
    netto_summe NUMERIC(12, 2) NOT NULL DEFAULT 0,
    steuer_summe NUMERIC(12, 2) NOT NULL DEFAULT 0,
    brutto_summe NUMERIC(12, 2) NOT NULL DEFAULT 0,
    dokument_id UUID REFERENCES vorgang_dokument(id) ON DELETE SET NULL,
    empfaenger_email TEXT,
    versendet_at TIMESTAMPTZ,
    versendet_von UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rabatt ist je Position frei wählbar zwischen Prozent und Euro-Betrag
-- (Produktentscheidung 2026-08-18, siehe Tech Design Abschnitt E).
CREATE TABLE IF NOT EXISTS angebot_position (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    angebot_id UUID NOT NULL REFERENCES angebot(id) ON DELETE CASCADE,
    bezeichnung TEXT NOT NULL,
    menge NUMERIC(12, 2) NOT NULL,
    einheit TEXT NOT NULL,
    einzelpreis NUMERIC(12, 2) NOT NULL,
    steuersatz NUMERIC(5, 2) NOT NULL,
    rabatt_typ TEXT NOT NULL DEFAULT 'prozent' CHECK (rabatt_typ IN ('prozent', 'betrag')),
    rabatt_wert NUMERIC(12, 2) NOT NULL DEFAULT 0,
    sortierung INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE angebot_nummernkreis ENABLE ROW LEVEL SECURITY;
ALTER TABLE angebot ENABLE ROW LEVEL SECURITY;
ALTER TABLE angebot_position ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS angebot_nummernkreis_isolation ON angebot_nummernkreis;
DROP POLICY IF EXISTS angebot_isolation ON angebot;
DROP POLICY IF EXISTS angebot_position_isolation ON angebot_position;

CREATE POLICY angebot_nummernkreis_isolation ON angebot_nummernkreis
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY angebot_isolation ON angebot
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY angebot_position_isolation ON angebot_position
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE INDEX IF NOT EXISTS idx_angebot_vorgang ON angebot(mandant_id, vorgang_id, created_at);
CREATE INDEX IF NOT EXISTS idx_angebot_vorgaenger ON angebot(mandant_id, vorgaenger_angebot_id);
CREATE INDEX IF NOT EXISTS idx_angebot_position_angebot ON angebot_position(mandant_id, angebot_id, sortierung);
