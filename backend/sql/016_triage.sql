-- PROJ-15: Auto-Triage mit Ampel.
-- Mandantentrennung über mandant_id + RLS auf current_setting('app.current_mandant_id').
-- Die Triage-Bewertung selbst wird nicht gespeichert (berechnet bei jedem Read),
-- hier nur die Inhaber-Konfiguration (Feldbezüge, Wertklassifikationen, Kapazität).
--
-- Muster: website_settings (backend/sql/002_website.sql) — genau eine Zeile je
-- Mandant über UNIQUE(mandant_id); Fremd-IDs werden im Service gegen den
-- veröffentlichten Formular-Snapshot geprüft (kein FK auf formular_feld, da
-- der Snapshot die stabile Quelle ist).

CREATE TABLE IF NOT EXISTS triage_einstellung (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL UNIQUE REFERENCES mandanten(id) ON DELETE CASCADE,
    -- Bezug zum veröffentlichten Anfrageformular (nur dessen Leistungsfeld zählt).
    leistungs_formular_id UUID,
    leistungs_feld_id UUID,
    -- Optionales zweites Feld derselben veröffentlichten Form (Wunschtermin).
    wunschtermin_feld_id UUID,
    -- Kapazitätsangabe „Nächster freier Termin“ (Inhaber).
    naechster_freier_termin DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS triage_leistungswert (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    einstellung_id UUID NOT NULL REFERENCES triage_einstellung(id) ON DELETE CASCADE,
    -- Stabile Optionswerte (nicht Label) der Leistungsauswahl.
    wert TEXT NOT NULL,
    klassifikation TEXT NOT NULL CHECK (klassifikation IN ('passend', 'unpassend')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (einstellung_id, wert)
);

-- ---------------------------------------------------------------------------
-- Row Level Security (jede mandantenbezogene Tabelle)
-- ---------------------------------------------------------------------------
ALTER TABLE triage_einstellung ENABLE ROW LEVEL SECURITY;
ALTER TABLE triage_leistungswert ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS triage_einstellung_isolation ON triage_einstellung;
DROP POLICY IF EXISTS triage_leistungswert_isolation ON triage_leistungswert;

CREATE POLICY triage_einstellung_isolation ON triage_einstellung
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY triage_leistungswert_isolation ON triage_leistungswert
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

-- ---------------------------------------------------------------------------
-- Indizes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_triage_einstellung_mandant ON triage_einstellung(mandant_id);
CREATE INDEX IF NOT EXISTS idx_triage_leistungswert_einstellung
    ON triage_leistungswert(einstellung_id);
CREATE INDEX IF NOT EXISTS idx_triage_leistungswert_mandant
    ON triage_leistungswert(mandant_id);
