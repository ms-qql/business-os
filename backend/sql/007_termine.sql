-- PROJ-6: Terminplanung und Teamzuweisung.
-- Eigenständige 1:n-Struktur auf Terminebene (ein Termin gehört zu genau einem
-- Vorgang, kann einem oder mehreren Monteuren zugewiesen werden). Konkurriert
-- nicht mit vorgang.zugewiesener_nutzer_id (Vorgangsebene), beide bleiben bestehen.
-- Mandantentrennung + RLS wie in 003_kunden_vorgaenge.sql; keine $$/DO-Blöcke
-- (SQLite-Testengine in db.py splittet an ';' — siehe Tech-Entscheidungen PROJ-6).

CREATE TABLE IF NOT EXISTS termin (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    vorgang_id UUID NOT NULL REFERENCES vorgang(id) ON DELETE RESTRICT,
    beginn TIMESTAMPTZ NOT NULL,
    ende TIMESTAMPTZ NOT NULL,
    adresse TEXT,
    notiz TEXT,
    abgesagt_at TIMESTAMPTZ,
    -- Snapshot des Vorgangsstatus, bevor dieser auf "Termin geplant" gesetzt wurde
    -- (AC-6: Rücksetzung bei Absage des letzten offenen Termins, historisiert).
    vorheriger_vorgang_status TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT termin_zeit_check CHECK (ende > beginn)
);

CREATE TABLE IF NOT EXISTS termin_zuweisung (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    termin_id UUID NOT NULL REFERENCES termin(id) ON DELETE CASCADE,
    nutzer_id UUID NOT NULL REFERENCES nutzer(id) ON DELETE RESTRICT,
    aktiv BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (termin_id, nutzer_id)
);

ALTER TABLE termin ENABLE ROW LEVEL SECURITY;
ALTER TABLE termin_zuweisung ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS termin_isolation ON termin;
DROP POLICY IF EXISTS termin_zuweisung_isolation ON termin_zuweisung;

CREATE POLICY termin_isolation ON termin
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY termin_zuweisung_isolation ON termin_zuweisung
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE INDEX IF NOT EXISTS idx_termin_mandant_beginn ON termin(mandant_id, beginn);
CREATE INDEX IF NOT EXISTS idx_termin_vorgang ON termin(mandant_id, vorgang_id);
CREATE INDEX IF NOT EXISTS idx_termin_zuweisung_nutzer_beginn ON termin_zuweisung(mandant_id, nutzer_id, created_at);
CREATE INDEX IF NOT EXISTS idx_termin_zuweisung_termin ON termin_zuweisung(mandant_id, termin_id);
