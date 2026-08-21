-- PROJ-8: PDF-Rechnungen und Rechnungsdokumente.
-- Eigenständige Rechnungsdomäne (ADR-8-1) neben angebote. Jede Fachtabelle
-- trägt mandant_id und ist per RLS auf current_setting('app.current_mandant_id')
-- begrenzt. Das erzeugte PDF liegt in vorgang_dokument/MinIO
-- (rechnung_fassung.dokument_id verweist darauf) — kein zweiter Dateispeicherpfad.
-- Die unveränderliche Belegfassung wird als JSON-Snapshot in rechnung_fassung
-- gehalten (ADR-8-2): Rechnungs-Kopf, Rechnungssteller-, Kunden-/Objekt-Snapshot,
-- Positionen und Summen. Spätere Stammdatenänderungen berühren sie nie.

-- Zähler pro Mandant für lückenlose, mandantengetrennte Rechnungsnummern.
-- Wird transaktional per SELECT ... FOR UPDATE hochgezählt (siehe
-- app/features/rechnungen/repository.py::next_rechnung_nummer).
CREATE TABLE IF NOT EXISTS rechnung_nummernkreis (
    mandant_id UUID PRIMARY KEY REFERENCES mandanten(id) ON DELETE CASCADE,
    letzte_nummer INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rechnungsstellerprofil (
    mandant_id UUID PRIMARY KEY REFERENCES mandanten(id) ON DELETE CASCADE,
    firma_name TEXT NOT NULL,
    strasse TEXT NOT NULL,
    hausnummer TEXT NOT NULL,
    plz TEXT NOT NULL,
    ort TEXT NOT NULL,
    steuernummer TEXT,
    ust_id TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rechnung (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    vorgang_id UUID NOT NULL REFERENCES vorgang(id) ON DELETE CASCADE,
    rechnungsnummer TEXT NOT NULL,
    rechnungsdatum DATE NOT NULL,
    leistungsdatum DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf', 'versendet', 'storniert')),
    zahlungsstatus TEXT NOT NULL DEFAULT 'Offen' CHECK (zahlungsstatus IN ('Offen', 'Bezahlt', 'Storniert')),
    netto_summe NUMERIC(12, 2) NOT NULL DEFAULT 0,
    steuer_summe NUMERIC(12, 2) NOT NULL DEFAULT 0,
    brutto_summe NUMERIC(12, 2) NOT NULL DEFAULT 0,
    empfaenger_email TEXT,
    fassung_id UUID,
    freigabe_vorbereitet_at TIMESTAMPTZ,
    versendet_at TIMESTAMPTZ,
    versendet_von UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    storniert_at TIMESTAMPTZ,
    storniert_von UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, rechnungsnummer)
);

CREATE TABLE IF NOT EXISTS rechnung_position (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    rechnung_id UUID NOT NULL REFERENCES rechnung(id) ON DELETE CASCADE,
    bezeichnung TEXT NOT NULL,
    menge NUMERIC(12, 2) NOT NULL,
    einheit TEXT NOT NULL,
    netto_einzelpreis NUMERIC(12, 2) NOT NULL,
    steuersatz NUMERIC(5, 2) NOT NULL,
    sortierung INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Genau eine unveränderliche Fassung je versendeter Rechnung (ADR-8-2).
CREATE TABLE IF NOT EXISTS rechnung_fassung (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    rechnung_id UUID NOT NULL REFERENCES rechnung(id) ON DELETE CASCADE,
    rechnungsnummer TEXT NOT NULL,
    kopf_json JSONB NOT NULL,
    rechnungssteller_json JSONB NOT NULL,
    kunde_json JSONB NOT NULL,
    objekt_json JSONB NOT NULL,
    positionen_json JSONB NOT NULL,
    summen_json JSONB NOT NULL,
    dokument_id UUID REFERENCES vorgang_dokument(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'rechnung_fassung_id_fkey'
    ) THEN
        ALTER TABLE rechnung
            ADD CONSTRAINT rechnung_fassung_id_fkey
            FOREIGN KEY (fassung_id) REFERENCES rechnung_fassung(id) ON DELETE SET NULL;
    END IF;
END $$;

ALTER TABLE rechnung_nummernkreis ENABLE ROW LEVEL SECURITY;
ALTER TABLE rechnungsstellerprofil ENABLE ROW LEVEL SECURITY;
ALTER TABLE rechnung ENABLE ROW LEVEL SECURITY;
ALTER TABLE rechnung_position ENABLE ROW LEVEL SECURITY;
ALTER TABLE rechnung_fassung ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rechnung_nummernkreis_isolation ON rechnung_nummernkreis;
DROP POLICY IF EXISTS rechnungsstellerprofil_isolation ON rechnungsstellerprofil;
DROP POLICY IF EXISTS rechnung_isolation ON rechnung;
DROP POLICY IF EXISTS rechnung_position_isolation ON rechnung_position;
DROP POLICY IF EXISTS rechnung_fassung_isolation ON rechnung_fassung;

CREATE POLICY rechnung_nummernkreis_isolation ON rechnung_nummernkreis
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY rechnungsstellerprofil_isolation ON rechnungsstellerprofil
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY rechnung_isolation ON rechnung
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY rechnung_position_isolation ON rechnung_position
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY rechnung_fassung_isolation ON rechnung_fassung
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE INDEX IF NOT EXISTS idx_rechnung_vorgang ON rechnung(mandant_id, vorgang_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rechnung_position_rechnung ON rechnung_position(mandant_id, rechnung_id, sortierung);
CREATE INDEX IF NOT EXISTS idx_rechnung_fassung_rechnung ON rechnung_fassung(mandant_id, rechnung_id);
