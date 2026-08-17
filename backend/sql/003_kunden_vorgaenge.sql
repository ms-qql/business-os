-- PROJ-3: Kunden, Objekte, Vorgänge und Dokumente.
-- Gleiches Muster wie 001_init.sql / 002_website.sql: jede Fachtabelle trägt
-- mandant_id und ist per RLS auf current_setting('app.current_mandant_id')
-- begrenzt. Die Löschsperre für Kunden mit bestehenden Vorgängen wird zusätzlich
-- über ON DELETE RESTRICT als zweite Verteidigungslinie erzwungen (die Anwendung
-- prüft vorab und liefert eine sprechende 409-Fehlermeldung).

CREATE TABLE IF NOT EXISTS kunde (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    telefon TEXT,
    notiz TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Objekt gehört zu einem Kunden und enthält die Einsatzadresse. Es ist als
-- Ganzes optional am Vorgang (vorgang.objekt_id ist NULLABLE), damit auch eine
-- noch unqualifizierte Anfrage sofort als Vorgang erfasst werden kann.
CREATE TABLE IF NOT EXISTS objekt (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    kunde_id UUID NOT NULL REFERENCES kunde(id) ON DELETE CASCADE,
    adresse TEXT NOT NULL,
    notiz TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vorgang (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    kunde_id UUID NOT NULL REFERENCES kunde(id) ON DELETE RESTRICT,
    objekt_id UUID REFERENCES objekt(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'Neu'
        CHECK (status IN ('Neu', 'Rückruf', 'Angebot offen', 'Termin geplant', 'Erledigt', 'Abgeschlossen')),
    quelle TEXT NOT NULL DEFAULT 'Sonstiges',
    anliegen TEXT NOT NULL,
    notizen TEXT,
    -- Minimales Zuweisungskonzept als Vorgriff auf PROJ-6 (Terminplanung/Team-
    -- zuweisung baut hierauf auf, siehe Tech Design). Grundlage der Monteur-
    -- Leseberechtigung: ein Monteur sieht nur den ihm zugewiesenen Vorgang.
    zugewiesener_nutzer_id UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unveränderliche, chronologische Ereignisse: Anlage, Feldänderungen,
-- Statuswechsel, Zuweisungen, Dokumentaktionen.
CREATE TABLE IF NOT EXISTS vorgang_historie (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    vorgang_id UUID NOT NULL REFERENCES vorgang(id) ON DELETE CASCADE,
    ereignis TEXT NOT NULL,
    detail TEXT,
    nutzer_id UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Dokument/Anhang: DB hält nur Dateimetadaten und den internen MinIO-
-- Objektschlüssel, keine öffentliche URL (gleiches Muster wie anfragebild /
-- website_settings.logo_objektpfad in 002_website.sql).
CREATE TABLE IF NOT EXISTS vorgang_dokument (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    vorgang_id UUID NOT NULL REFERENCES vorgang(id) ON DELETE CASCADE,
    dateiname TEXT NOT NULL,
    objektpfad TEXT NOT NULL,
    content_type TEXT NOT NULL,
    groesse_bytes INTEGER NOT NULL,
    hochgeladen_von UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Verknüpfung der bestehenden Website-Anfrage (PROJ-2) zum daraus entstandenen
-- Vorgang. anfrage/anfragebild existieren bereits (002_website.sql); der dortige
-- Kommentar kündigt diese Nachrüstung ausdrücklich an.
ALTER TABLE anfrage ADD COLUMN IF NOT EXISTS vorgang_id UUID REFERENCES vorgang(id) ON DELETE SET NULL;

ALTER TABLE kunde ENABLE ROW LEVEL SECURITY;
ALTER TABLE objekt ENABLE ROW LEVEL SECURITY;
ALTER TABLE vorgang ENABLE ROW LEVEL SECURITY;
ALTER TABLE vorgang_historie ENABLE ROW LEVEL SECURITY;
ALTER TABLE vorgang_dokument ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS kunde_isolation ON kunde;
DROP POLICY IF EXISTS objekt_isolation ON objekt;
DROP POLICY IF EXISTS vorgang_isolation ON vorgang;
DROP POLICY IF EXISTS vorgang_historie_isolation ON vorgang_historie;
DROP POLICY IF EXISTS vorgang_dokument_isolation ON vorgang_dokument;

CREATE POLICY kunde_isolation ON kunde
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY objekt_isolation ON objekt
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY vorgang_isolation ON vorgang
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY vorgang_historie_isolation ON vorgang_historie
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY vorgang_dokument_isolation ON vorgang_dokument
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE INDEX IF NOT EXISTS idx_kunde_mandant ON kunde(mandant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_kunde_email ON kunde(mandant_id, email);
CREATE INDEX IF NOT EXISTS idx_kunde_telefon ON kunde(mandant_id, telefon);
CREATE INDEX IF NOT EXISTS idx_objekt_kunde ON objekt(mandant_id, kunde_id);
CREATE INDEX IF NOT EXISTS idx_vorgang_mandant ON vorgang(mandant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_vorgang_status ON vorgang(mandant_id, status);
CREATE INDEX IF NOT EXISTS idx_vorgang_kunde ON vorgang(mandant_id, kunde_id);
CREATE INDEX IF NOT EXISTS idx_vorgang_zugewiesen ON vorgang(mandant_id, zugewiesener_nutzer_id);
CREATE INDEX IF NOT EXISTS idx_vorgang_historie_vorgang ON vorgang_historie(vorgang_id, created_at);
CREATE INDEX IF NOT EXISTS idx_vorgang_dokument_vorgang ON vorgang_dokument(vorgang_id, created_at);
CREATE INDEX IF NOT EXISTS idx_anfrage_vorgang ON anfrage(vorgang_id);
