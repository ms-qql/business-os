-- PROJ-2: Geführte SHK-Website, Branding und Anfrageformular.
-- Öffentliche Endpunkte lösen den Mandanten ausschließlich über
-- website_domains auf (nie über Client-/Formulareingaben).

CREATE TABLE IF NOT EXISTS website_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL UNIQUE REFERENCES mandanten(id) ON DELETE CASCADE,
    firmenname TEXT NOT NULL DEFAULT '',
    logo_objektpfad TEXT,
    marken_farbe TEXT,
    telefon TEXT,
    email TEXT,
    adresse TEXT,
    oeffnungszeiten TEXT,
    ueber_uns TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS website_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    hostname TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'aktiv' CHECK (status IN ('aktiv', 'inaktiv')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leistungsseite (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    titel TEXT NOT NULL,
    aktiv BOOLEAN NOT NULL DEFAULT FALSE,
    kurzbeschreibung TEXT NOT NULL DEFAULT '',
    inhalt TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, slug)
);

-- Eigenständige Tabelle (kein Bezug zu vorgang — PROJ-3 existiert im Code noch
-- nicht und wird bei Einführung migriert/verknüpft, nicht vorweggenommen).
CREATE TABLE IF NOT EXISTS anfrage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kontaktweg TEXT NOT NULL CHECK (kontaktweg IN ('Telefon', 'E-Mail')),
    telefon TEXT,
    email TEXT,
    adresse TEXT NOT NULL,
    anliegen TEXT NOT NULL,
    dringlichkeit TEXT NOT NULL CHECK (dringlichkeit IN ('Normal', 'Dringend')),
    zeitfenster TEXT,
    quelle TEXT NOT NULL DEFAULT 'Website',
    uebermittlungskennung TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, uebermittlungskennung)
);

CREATE TABLE IF NOT EXISTS anfragebild (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    anfrage_id UUID REFERENCES anfrage(id) ON DELETE CASCADE,
    uebermittlungskennung TEXT NOT NULL,
    objektpfad TEXT NOT NULL,
    dateiname TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rate-Limit nach Vorbild login_versuche (backend/sql/001_init.sql) — kein
-- Rate-Limit-Paket im Code, keine neue Drittanbieter-Abhängigkeit.
CREATE TABLE IF NOT EXISTS website_anfrage_versuche (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE website_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE leistungsseite ENABLE ROW LEVEL SECURITY;
ALTER TABLE anfrage ENABLE ROW LEVEL SECURITY;
ALTER TABLE anfragebild ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS website_settings_isolation ON website_settings;
DROP POLICY IF EXISTS website_domains_isolation ON website_domains;
DROP POLICY IF EXISTS leistungsseite_isolation ON leistungsseite;
DROP POLICY IF EXISTS anfrage_isolation ON anfrage;
DROP POLICY IF EXISTS anfragebild_isolation ON anfragebild;

CREATE POLICY website_settings_isolation ON website_settings
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY website_domains_isolation ON website_domains
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY leistungsseite_isolation ON leistungsseite
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY anfrage_isolation ON anfrage
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY anfragebild_isolation ON anfragebild
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

-- Domainauflösung für öffentliche Endpunkte braucht den Mandanten anhand des
-- Hostnamens, bevor ein Mandantenkontext gesetzt ist. SECURITY DEFINER
-- umgeht RLS gezielt nur für diese eine Suche (analog
-- auth_find_user_by_email in 001_init.sql).
CREATE OR REPLACE FUNCTION website_find_mandant_by_hostname(p_hostname TEXT)
RETURNS TABLE (mandant_id UUID) LANGUAGE sql SECURITY DEFINER AS $$
    SELECT wd.mandant_id
    FROM website_domains wd
    JOIN mandanten m ON m.id = wd.mandant_id
    WHERE wd.hostname = p_hostname AND wd.status = 'aktiv' AND m.status = 'active';
$$;

CREATE INDEX IF NOT EXISTS idx_website_settings_mandant ON website_settings(mandant_id);
CREATE INDEX IF NOT EXISTS idx_website_domains_hostname ON website_domains(hostname);
CREATE INDEX IF NOT EXISTS idx_website_domains_mandant ON website_domains(mandant_id);
CREATE INDEX IF NOT EXISTS idx_leistungsseite_mandant ON leistungsseite(mandant_id, slug);
CREATE INDEX IF NOT EXISTS idx_anfrage_mandant ON anfrage(mandant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_anfrage_kennung ON anfrage(mandant_id, uebermittlungskennung);
CREATE INDEX IF NOT EXISTS idx_anfragebild_anfrage ON anfragebild(anfrage_id);
CREATE INDEX IF NOT EXISTS idx_anfragebild_kennung ON anfragebild(mandant_id, uebermittlungskennung);
CREATE INDEX IF NOT EXISTS idx_website_anfrage_versuche_ip ON website_anfrage_versuche(ip, created_at);
