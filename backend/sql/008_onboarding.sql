-- PROJ-7: Begleitetes Onboarding (Betriebsdaten, Branding, Postfach).
-- Rohdaten-getriebene Onboarding-Statusberechnung, versionsgebundener
-- Postfach-Testnachweis, Testvorgang-Markierung + kaskadierende Löschliste,
-- sowie die Ersteinrichtungs-Preisliste. Alle neuen Tabellen tragen
-- mandant_id und sind per RLS auf current_setting('app.current_mandant_id')
-- begrenzt (gleiches Muster wie die vorherigen Migrationen).

-- 1) email_konto: monotone Konfigurationsversion. Jede erfolgreiche Änderung
--    über PUT /email-konto erhöht die Version; ein gespeicherter Testnachweis
--    gilt nur, wenn seine konfiguration_version zur aktuellen Version passt.
--    Bestandszeilen starten bei 1 (Design: ADR-7-3).
ALTER TABLE email_konto ADD COLUMN IF NOT EXISTS konfiguration_version INTEGER NOT NULL DEFAULT 1;

-- 2) vorgang: Testkennzeichen. Ein Onboarding-Testvorgang wird mit ist_test=true
--    angelegt und aus Listen/Auswertungen/Nummernkreisen ausgeschlossen.
ALTER TABLE vorgang ADD COLUMN IF NOT EXISTS ist_test BOOLEAN NOT NULL DEFAULT FALSE;

-- 3) onboarding_postfach_test: mandant-gebundener Nachweis eines Tests der
--    gespeicherten Postfachkonfiguration. Keine Geheimnisse — nur Ergebnis +
--    die Version, gegen die geprüft wurde.
CREATE TABLE IF NOT EXISTS onboarding_postfach_test (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    email_konto_id UUID NOT NULL REFERENCES email_konto(id) ON DELETE CASCADE,
    konfiguration_version INTEGER NOT NULL,
    imap_ok BOOLEAN NOT NULL,
    smtp_ok BOOLEAN NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    getestet_von UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4) onboarding_testvorgang: Zuordnung des vom Onboarding erzeugten Vorgangs zu
--    seinen Test-Stammdaten. Sie ist die sichere Löschliste: nur genau diese
--    vom Onboarding angelegten Daten (Kunde, Objekt, Vorgang, Threads,
--    Nachrichten, Dokumente) dürfen zusammen entfernt werden.
CREATE TABLE IF NOT EXISTS onboarding_testvorgang (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    vorgang_id UUID NOT NULL REFERENCES vorgang(id) ON DELETE CASCADE,
    kunde_id UUID NOT NULL REFERENCES kunde(id) ON DELETE CASCADE,
    objekt_id UUID REFERENCES objekt(id) ON DELETE SET NULL,
    anfrage_id UUID REFERENCES anfrage(id) ON DELETE SET NULL,
    erstellt_von UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (vorgang_id)
);

-- 5) preisliste: Ersteinrichtungs-Katalogpositionen (PROJ-7 Schritt 6).
--    Diese Tabelle liefert die Quelle für angebots_position in PROJ-5; sie ist
--    bewusst eigenständig (Architektur-Entscheidung offen gelassen, hier die
--    einfachere eigenständige Tabelle gewählt, siehe Tech Design Abschnitt
--    Technical Requirements).
CREATE TABLE IF NOT EXISTS preisliste (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    bezeichnung TEXT NOT NULL,
    einheit TEXT NOT NULL DEFAULT 'Stück',
    netto_einzelpreis NUMERIC(12, 2) NOT NULL DEFAULT 0,
    steuersatz NUMERIC(5, 2) NOT NULL DEFAULT 19,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6) website_domains: Zeitpunkt der Veröffentlichung (PROJ-7 Veröffentlichen).
ALTER TABLE website_domains ADD COLUMN IF NOT EXISTS veröffentlicht_am TIMESTAMPTZ;

-- RLS für alle neuen Tabellen.
ALTER TABLE onboarding_postfach_test ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_testvorgang ENABLE ROW LEVEL SECURITY;
ALTER TABLE preisliste ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS onboarding_postfach_test_isolation ON onboarding_postfach_test;
DROP POLICY IF EXISTS onboarding_testvorgang_isolation ON onboarding_testvorgang;
DROP POLICY IF EXISTS preisliste_isolation ON preisliste;

CREATE POLICY onboarding_postfach_test_isolation ON onboarding_postfach_test
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY onboarding_testvorgang_isolation ON onboarding_testvorgang
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY preisliste_isolation ON preisliste
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

-- Index: aktuellster gültiger Test pro Konto (Version-Match).
CREATE INDEX IF NOT EXISTS idx_onboarding_postfach_test_konto
    ON onboarding_postfach_test(mandant_id, email_konto_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_onboarding_testvorgang_mandant
    ON onboarding_testvorgang(mandant_id, vorgang_id);
CREATE INDEX IF NOT EXISTS idx_preisliste_mandant ON preisliste(mandant_id, bezeichnung);
CREATE INDEX IF NOT EXISTS idx_vorgang_ist_test ON vorgang(mandant_id, ist_test);

-- Reservierungs-Kollisionsprüfung läuft serverseitig über alle Mandanten
-- hinweg (nicht innerhalb der RLS-Sicht des aufrufenden Mandanten). SECURITY
-- DEFINER umgeht RLS gezielt nur für diese eine Suche (analog
-- website_find_mandant_by_hostname in 002_website.sql).
CREATE OR REPLACE FUNCTION onboarding_hostname_owner(p_hostname TEXT)
RETURNS TABLE (mandant_id UUID) LANGUAGE sql SECURITY DEFINER AS $$
    SELECT wd.mandant_id FROM website_domains wd
    WHERE wd.hostname = p_hostname;
$$;
