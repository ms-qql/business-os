-- PROJ-13: Formular-Baukasten.
-- Mandantentrennung über mandant_id + RLS auf current_setting('app.current_mandant_id').
-- Entwurf (formular + formular_schritt + formular_feld + formular_option) ist editierbar;
-- formular_version ist der unveränderliche Publish-Snapshot; formular_einsendung /
-- formular_upload sind die öffentlichen Antwort- bzw. Upload-Datensätze.

-- ---------------------------------------------------------------------------
-- Entwurf: Formular-Kopf
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Neues Formular',
    komplexitaet TEXT NOT NULL DEFAULT 'einfach'
        CHECK (komplexitaet IN ('einfach', 'erweitert')),
    -- Optimistic concurrency: jede Mutation erhöht die Zahl; veraltete PATCHes
    -- werden mit 409 abgewiesen (gleiches Muster wie builder/version).
    draft_revision INTEGER NOT NULL DEFAULT 1,
    veroeffentlicht BOOLEAN NOT NULL DEFAULT FALSE,
    aktuelle_version_id UUID REFERENCES formular_version(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Entwurf: Schritte (lineare Reihenfolge pro Formular)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular_schritt (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    titel TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (formular_id, position)
);

-- ---------------------------------------------------------------------------
-- Entwurf: Felder (festgekoppelt an einen Schritt)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular_feld (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    schritt_id UUID NOT NULL REFERENCES formular_schritt(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    typ TEXT NOT NULL
        CHECK (typ IN ('text', 'mehrzeilig', 'dropdown', 'kachel', 'radio',
                       'zahl', 'datum', 'upload', 'adresse', 'consent')),
    label TEXT NOT NULL DEFAULT '',
    hilfetext TEXT,
    pflichtfeld BOOLEAN NOT NULL DEFAULT FALSE,
    -- Nur optionale Felder: in der öffentlichen „Einfach"-Stufe ausgeblendet,
    -- in „Erweitert" eingeblendet. Pflichtfelder sind immer sichtbar.
    optional_in_einfach BOOLEAN NOT NULL DEFAULT FALSE,
    -- Optionale Übernahme-Zuordnung in Vorgang/Anfrage (nur Text/Adresse/Auswahl).
    uebernahme TEXT CHECK (uebernahme IN ('kontaktname', 'email', 'telefon',
                                         'adresse', 'anliegen')),
    -- Typkonfiguration (nur jeweils zutreffende Spalten befüllt).
    min_val NUMERIC,
    max_val NUMERIC,
    ganzzahl BOOLEAN,
    reg_exp TEXT,
    maxlaenge INTEGER,
    datum_min TEXT,
    datum_max TEXT,
    max_anzahl INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (schritt_id, position)
);

-- ---------------------------------------------------------------------------
-- Entwurf: Auswahloptionen (nur dropdown/kachel/radio)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular_option (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    feld_id UUID NOT NULL REFERENCES formular_feld(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    label TEXT NOT NULL,
    wert TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (feld_id, position),
    -- Gespeicherter Wert eindeutig und nicht leer je Feld (Publish-Check stützt
    -- sich zusätzlich darauf, hier aber als Datenbank-Invariante abgesichert).
    CONSTRAINT formular_option_wert_nicht_leer CHECK (wert <> ''),
    CONSTRAINT formular_option_wert_eindeutig UNIQUE (feld_id, wert)
);

-- ---------------------------------------------------------------------------
-- Unveränderlicher Publish-Snapshot
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    -- Fortlaufende Nummer je Formular.
    nummer INTEGER NOT NULL,
    -- Zufällige, nicht erratbare ID für die öffentliche URL.
    public_id TEXT NOT NULL,
    -- Vollständiger, validierter Snapshot (Schritte/Felder/Optionen) als JSON.
    inhalt JSONB NOT NULL,
    veroeffentlicht_am TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    veroeffentlicht_von UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    UNIQUE (formular_id, nummer),
    UNIQUE (public_id)
);

-- ---------------------------------------------------------------------------
-- Öffentliche Einsendung (unveränderliche Antwort)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular_einsendung (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    version_id UUID NOT NULL REFERENCES formular_version(id) ON DELETE CASCADE,
    uebermittlungskennung TEXT NOT NULL,
    werte JSONB NOT NULL,
    consent_nachweis JSONB,
    spam_status TEXT NOT NULL DEFAULT 'normal'
        CHECK (spam_status IN ('normal', 'spam')),
    anfrage_id UUID REFERENCES anfrage(id) ON DELETE SET NULL,
    vorgang_id UUID REFERENCES vorgang(id) ON DELETE SET NULL,
    erstellt_am TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, uebermittlungskennung)
);

-- ---------------------------------------------------------------------------
-- Upload (temporär pro Kennung, bei Submit an Einsendung verknüpft)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular_upload (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    formular_id UUID NOT NULL REFERENCES formular(id) ON DELETE CASCADE,
    feld_id UUID REFERENCES formular_feld(id) ON DELETE SET NULL,
    uebermittlungskennung TEXT NOT NULL,
    einsendung_id UUID REFERENCES formular_einsendung(id) ON DELETE SET NULL,
    objektpfad TEXT NOT NULL,
    originalname TEXT NOT NULL,
    mime_typ TEXT NOT NULL,
    groesse_bytes INTEGER NOT NULL,
    erstellt_am TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Rate-Limit-Versuche für öffentliche Endpunkte (Muster: website_anfrage_versuche)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS formular_einsendung_versuche (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS formular_upload_versuche (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Erweiterung bestehender Tabellen
-- ---------------------------------------------------------------------------
ALTER TABLE anfrage ADD COLUMN IF NOT EXISTS formular_einsendung_id UUID
    REFERENCES formular_einsendung(id) ON DELETE SET NULL;

ALTER TABLE kunde ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'aktiv'
    CHECK (status IN ('entwurf', 'aktiv'));
-- Bestandskunden migrieren zu 'aktiv'.
UPDATE kunde SET status = 'aktiv' WHERE status IS NULL OR status = '';

-- ---------------------------------------------------------------------------
-- Row Level Security (jede mandantenbezogene Tabelle)
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- Indizes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_formular_mandant ON formular(mandant_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_formular_schritt_formular ON formular_schritt(formular_id, position);
CREATE INDEX IF NOT EXISTS idx_formular_feld_schritt ON formular_feld(schritt_id, position);
CREATE INDEX IF NOT EXISTS idx_formular_option_feld ON formular_option(feld_id, position);
CREATE INDEX IF NOT EXISTS idx_formular_version_formular ON formular_version(formular_id, nummer);
CREATE INDEX IF NOT EXISTS idx_formular_version_public_id ON formular_version(public_id);
CREATE INDEX IF NOT EXISTS idx_formular_einsendung_version ON formular_einsendung(version_id);
CREATE INDEX IF NOT EXISTS idx_formular_einsendung_kennung ON formular_einsendung(mandant_id, uebermittlungskennung);
CREATE INDEX IF NOT EXISTS idx_formular_einsendung_spam ON formular_einsendung(mandant_id, spam_status, erstellt_am);
CREATE INDEX IF NOT EXISTS idx_formular_upload_kennung ON formular_upload(mandant_id, uebermittlungskennung);
CREATE INDEX IF NOT EXISTS idx_formular_upload_einsendung ON formular_upload(einsendung_id);
CREATE INDEX IF NOT EXISTS idx_anfrage_einsendung ON anfrage(formular_einsendung_id);
CREATE INDEX IF NOT EXISTS idx_formular_einsendung_versuche_ip ON formular_einsendung_versuche(ip, created_at);
CREATE INDEX IF NOT EXISTS idx_formular_upload_versuche_ip ON formular_upload_versuche(ip, created_at);
