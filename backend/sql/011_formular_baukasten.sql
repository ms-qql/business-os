-- PROJ-13: Formular-Baukasten.
-- Neue mandantenbezogene Tabellen für den Formular-Editor (Entwurf),
-- unveränderliche Publish-Snapshots, öffentliche Einsendungen inkl.
-- Spam-Markierung und feldbezogene Uploads. Ergänzt bestehende anfrage
-- (formular_einsendung_id) und kunde (status 'entwurf'/'aktiv').
-- Roh-SQL-Konvention wie 001–010 (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS /
-- DROP POLICY IF EXISTS, keine Alembic).

CREATE TABLE IF NOT EXISTS formular (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Neues Formular',
    komplexitaetsstufe TEXT NOT NULL DEFAULT 'einfach'
        CHECK (komplexitaetsstufe IN ('einfach', 'erweitert')),
    draft_revision INTEGER NOT NULL DEFAULT 1,
    published_version_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS formular_schritt (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    titel TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, formular_id, position)
);

CREATE TABLE IF NOT EXISTS formular_feld (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    schritt_id UUID NOT NULL REFERENCES formular_schritt(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    typ TEXT NOT NULL CHECK (typ IN (
        'text', 'mehrzeilig', 'dropdown', 'kachel', 'radio',
        'zahl', 'datum', 'upload', 'adresse', 'consent'
    )),
    label TEXT NOT NULL DEFAULT '',
    hilfetext TEXT NOT NULL DEFAULT '',
    pflichtfeld BOOLEAN NOT NULL DEFAULT FALSE,
    optional_in_einfach BOOLEAN NOT NULL DEFAULT FALSE,
    konfiguration JSONB NOT NULL DEFAULT '{}'::jsonb,
    uebernahme TEXT CHECK (uebernahme IN (
        'kontaktname', 'email', 'telefon', 'adresse', 'anliegen'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, schritt_id, position)
);

CREATE TABLE IF NOT EXISTS formular_option (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    feld_id UUID NOT NULL REFERENCES formular_feld(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    wert TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, feld_id, position)
);

CREATE TABLE IF NOT EXISTS formular_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    nummer INTEGER NOT NULL,
    public_id UUID NOT NULL,
    snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    veroeffentlicht_am TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    veroeffentlicht_von UUID,
    zurueckgezogen BOOLEAN NOT NULL DEFAULT FALSE,
    zurueckgezogen_am TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, formular_id, nummer),
    UNIQUE (public_id)
);

CREATE TABLE IF NOT EXISTS formular_einsendung (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID REFERENCES formular(id) ON DELETE CASCADE,
    version_id UUID NOT NULL REFERENCES formular_version(id) ON DELETE CASCADE,
    uebermittlungskennung TEXT NOT NULL,
    werte JSONB NOT NULL DEFAULT '{}'::jsonb,
    consent_nachweis JSONB NOT NULL DEFAULT '{}'::jsonb,
    spam_status TEXT NOT NULL DEFAULT 'normal'
        CHECK (spam_status IN ('normal', 'spam')),
    anfrage_id UUID,
    vorgang_id UUID,
    eingegangen_am TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, uebermittlungskennung)
);

CREATE TABLE IF NOT EXISTS formular_upload (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    uebermittlungskennung TEXT NOT NULL,
    feld_id UUID NOT NULL,
    objektpfad TEXT NOT NULL,
    originalname TEXT NOT NULL DEFAULT '',
    mime_typ TEXT NOT NULL DEFAULT '',
    groesse_bytes INTEGER NOT NULL DEFAULT 0,
    einsendung_id UUID REFERENCES formular_einsendung(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bestehende anfrage um die optionale Formular-Einsendung erweitern
-- (eindeutige Beziehung: eine Anfrage höchstens aus einer Einsendung).
ALTER TABLE anfrage ADD COLUMN IF NOT EXISTS formular_einsendung_id UUID;
ALTER TABLE anfrage
    ADD CONSTRAINT IF NOT EXISTS fk_anfrage_formular_einsendung
    FOREIGN KEY (formular_einsendung_id) REFERENCES formular_einsendung(id) ON DELETE SET NULL;
ALTER TABLE anfrage
    ADD CONSTRAINT IF NOT EXISTS uq_anfrage_formular_einsendung
    UNIQUE (formular_einsendung_id);

-- Kunde um den Status 'entwurf'/'aktiv' erweitern (Bestand migriert zu 'aktiv').
ALTER TABLE kunde ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'aktiv'
    CHECK (status IN ('entwurf', 'aktiv'));

-- Row Level Security auf jeder mandantenbezogenen Tabelle.
ALTER TABLE formular ENABLE ROW LEVEL SECURITY;
ALTER TABLE formular_schritt ENABLE ROW LEVEL SECURITY;
ALTER TABLE formular_feld ENABLE ROW LEVEL SECURITY;
ALTER TABLE formular_option ENABLE ROW LEVEL SECURITY;
ALTER TABLE formular_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE formular_einsendung ENABLE ROW LEVEL SECURITY;
ALTER TABLE formular_upload ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS formular_isolation ON formular;
DROP POLICY IF EXISTS formular_schritt_isolation ON formular_schritt;
DROP POLICY IF EXISTS formular_feld_isolation ON formular_feld;
DROP POLICY IF EXISTS formular_option_isolation ON formular_option;
DROP POLICY IF EXISTS formular_version_isolation ON formular_version;
DROP POLICY IF EXISTS formular_einsendung_isolation ON formular_einsendung;
DROP POLICY IF EXISTS formular_upload_isolation ON formular_upload;

CREATE POLICY formular_isolation ON formular
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY formular_schritt_isolation ON formular_schritt
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY formular_feld_isolation ON formular_feld
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY formular_option_isolation ON formular_option
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY formular_version_isolation ON formular_version
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY formular_einsendung_isolation ON formular_einsendung
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY formular_upload_isolation ON formular_upload
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

-- Lesereihenfolge-Indizes.
CREATE INDEX IF NOT EXISTS idx_formular_mandant ON formular(mandant_id);
CREATE INDEX IF NOT EXISTS idx_formular_schritt_formular
    ON formular_schritt(formular_id, position);
CREATE INDEX IF NOT EXISTS idx_formular_feld_schritt
    ON formular_feld(schritt_id, position);
CREATE INDEX IF NOT EXISTS idx_formular_option_feld
    ON formular_option(feld_id, position);
CREATE INDEX IF NOT EXISTS idx_formular_version_formular
    ON formular_version(mandant_id, formular_id);
CREATE INDEX IF NOT EXISTS idx_formular_version_public
    ON formular_version(public_id);
CREATE INDEX IF NOT EXISTS idx_formular_einsendung_version
    ON formular_einsendung(mandant_id, version_id);
CREATE INDEX IF NOT EXISTS idx_formular_einsendung_kennung
    ON formular_einsendung(mandant_id, uebermittlungskennung);
CREATE INDEX IF NOT EXISTS idx_formular_upload_kennung
    ON formular_upload(mandant_id, uebermittlungskennung);
CREATE INDEX IF NOT EXISTS idx_formular_upload_einsendung
    ON formular_upload(einsendung_id);
