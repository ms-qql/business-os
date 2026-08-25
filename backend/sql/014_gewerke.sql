-- PROJ-22: Gewerke – Kalkulationseinheiten für Angebote.
-- Führt drei neue RLS-Katalogtabellen ein (Gewerk/Kategorie/Kostenzeile),
-- erweitert angebot_position um Kalkulations-/Override-Nachweise und migriert
-- die bestehende preisliste einmalig in Null-Zuschlag-Gewerke. Vorhandene
-- Angebotspositionen bleiben unverändert (keine Live-Referenz, ADR-22-2).
--
-- Reihenfolge: Tabellen + Erweiterung zuerst, dann Datenmigration, dann
-- Indizes/Policies (wie in 006_angebote.sql / 008_onboarding.sql).

-- 1) gewerk_kategorie: mandanteneigene Namensklammer für Gewerke.
CREATE TABLE IF NOT EXISTS gewerk_kategorie (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) gewerk: wiederverwendbare Kalkulationseinheit.
--    kalkulationsart: 'je_einheit' (VK = Positions-Einzelpreis) oder
--    'gesamtpreis' (eine Position mit Menge 1, VK = Einzel-/Gesamtpreis).
CREATE TABLE IF NOT EXISTS gewerk (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    kategorie_id UUID REFERENCES gewerk_kategorie(id) ON DELETE SET NULL,
    bezeichnung TEXT NOT NULL,
    langbeschreibung TEXT,
    einheit TEXT NOT NULL,
    kalkulationsart TEXT NOT NULL DEFAULT 'je_einheit'
        CHECK (kalkulationsart IN ('je_einheit', 'gesamtpreis')),
    steuersatz NUMERIC(5, 2) NOT NULL DEFAULT 19,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3) gewerk_kostenzeile: genau eine Kostenart je Zeile, keine freien
--    Kostenarten (ADR-22-1). EK > 0, Menge > 0, Zuschlag >= 0.
CREATE TABLE IF NOT EXISTS gewerk_kostenzeile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    gewerk_id UUID NOT NULL REFERENCES gewerk(id) ON DELETE CASCADE,
    kostenart TEXT NOT NULL
        CHECK (kostenart IN ('lohn', 'material', 'fremdleistung', 'sonstiges_geraete')),
    beschreibung TEXT,
    menge NUMERIC(12, 3) NOT NULL CHECK (menge > 0),
    einheit TEXT NOT NULL,
    ek_einzelpreis NUMERIC(12, 2) NOT NULL CHECK (ek_einzelpreis > 0),
    zuschlag_prozent NUMERIC(8, 2) NOT NULL DEFAULT 0 CHECK (zuschlag_prozent >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4) angebot_position: Kalkulations-Snapshot + Override-Nachweis.
--    kalkulierter_einzelpreis: Ausgangswert aus dem Gewerk (NULL bei manueller
--    Position). preis_override_begruendung: interne Begründung, erscheint
--    NICHT im Kunden-PDF (ADR-22-3). Beide Felder nullable.
ALTER TABLE angebot_position
    ADD COLUMN IF NOT EXISTS kalkulierter_einzelpreis NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS preis_override_begruendung TEXT;

-- 5) Migration der bestehenden preisliste in Null-Zuschlag-Gewerke.
--    Jede preisliste-Zeile wird ein Gewerk ohne Kategorie, Einheit wie
--    bisher, EK = netto_einzelpreis, 0 % Zuschlag und eine einzige
--    Kostenzeile 'sonstiges_geraete'. Historische Angebotspositionen bleiben
--    unberührt — sie referenzieren kein Gewerk. Idempotent via NOT EXISTS.
INSERT INTO gewerk (id, mandant_id, kategorie_id, bezeichnung, langbeschreibung,
                    einheit, kalkulationsart, steuersatz, created_at, updated_at)
SELECT gen_random_uuid(), p.mandant_id, NULL, p.bezeichnung, NULL,
       p.einheit, 'je_einheit', p.steuersatz, p.created_at, p.updated_at
FROM preisliste p
WHERE NOT EXISTS (
    SELECT 1 FROM gewerk g
    WHERE g.mandant_id = p.mandant_id AND g.bezeichnung = p.bezeichnung
      AND g.einheit = p.einheit
);

-- Kostenzeilen zu den soeben migrierten Gewerken. Die Gewerke sind über
-- (mandant_id, bezeichnung, einheit) eindeutig bestimmbar; pro preisliste-
-- Zeile genau eine Kostenzeile 'sonstiges_geraete' mit EK = netto_einzelpreis.
INSERT INTO gewerk_kostenzeile (id, mandant_id, gewerk_id, kostenart, menge,
                                einheit, ek_einzelpreis, zuschlag_prozent,
                                created_at, updated_at)
SELECT gen_random_uuid(), p.mandant_id, g.id, 'sonstiges_geraete', 1.0,
       p.einheit, p.netto_einzelpreis, 0.0, p.created_at, p.updated_at
FROM preisliste p
JOIN gewerk g
  ON g.mandant_id = p.mandant_id AND g.bezeichnung = p.bezeichnung
     AND g.einheit = p.einheit
WHERE NOT EXISTS (
    SELECT 1 FROM gewerk_kostenzeile kz
    WHERE kz.gewerk_id = g.id
);

-- 6) RLS für alle neuen Tabellen (gleiches Muster wie 006/008).
ALTER TABLE gewerk_kategorie ENABLE ROW LEVEL SECURITY;
ALTER TABLE gewerk ENABLE ROW LEVEL SECURITY;
ALTER TABLE gewerk_kostenzeile ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS gewerk_kategorie_isolation ON gewerk_kategorie;
DROP POLICY IF EXISTS gewerk_isolation ON gewerk;
DROP POLICY IF EXISTS gewerk_kostenzeile_isolation ON gewerk_kostenzeile;

CREATE POLICY gewerk_kategorie_isolation ON gewerk_kategorie
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY gewerk_isolation ON gewerk
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY gewerk_kostenzeile_isolation ON gewerk_kostenzeile
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

-- 7) Indexe: Kategorien je Mandant, Gewerke je Kategorie/Mandant und
--    Duplikatprüfung (bezeichnung + einheit je Mandant).
CREATE INDEX IF NOT EXISTS idx_gewerk_kategorie_mandant
    ON gewerk_kategorie(mandant_id, name);
CREATE INDEX IF NOT EXISTS idx_gewerk_mandant_kategorie
    ON gewerk(mandant_id, kategorie_id);
CREATE INDEX IF NOT EXISTS idx_gewerk_mandant_bezeichnung
    ON gewerk(mandant_id, bezeichnung, einheit);
CREATE INDEX IF NOT EXISTS idx_gewerk_kostenzeile_gewerk
    ON gewerk_kostenzeile(mandant_id, gewerk_id);
