-- PROJ-1: Mandanten, Anmeldung, Rollen — Schema mit Row Level Security.
-- Alle geschäftlichen Tabellen tragen mandant_id und sind per RLS auf den
-- je Transaktion gesetzten Kontext (app.current_mandant_id) begrenzt.

CREATE TABLE IF NOT EXISTS mandanten (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nutzer (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT,
    role TEXT NOT NULL CHECK (role IN ('Inhaber', 'Buero', 'Monteur')),
    status TEXT NOT NULL DEFAULT 'invited'
        CHECK (status IN ('active', 'invited', 'disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, email)
);

CREATE TABLE IF NOT EXISTS sitzungen (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    nutzer_id UUID NOT NULL REFERENCES nutzer(id) ON DELETE CASCADE,
    ip TEXT,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS einladungen (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    nutzer_id UUID NOT NULL REFERENCES nutzer(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS passwort_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    nutzer_id UUID NOT NULL REFERENCES nutzer(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS login_versuche (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    ip TEXT,
    erfolg BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    nutzer_id UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    typ TEXT NOT NULL,
    erfolg BOOLEAN NOT NULL,
    detail TEXT,
    ip TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Plattformbetreiber: außerhalb der Mandantenwelt, KEINE RLS (Zugriff nur über
-- eigene Token-Audience + Routen-Guards).
CREATE TABLE IF NOT EXISTS betreiber (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS betreiber_sitzungen (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    betreiber_id UUID NOT NULL REFERENCES betreiber(id) ON DELETE CASCADE,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS für alle mandantenbezogenen Tabellen.
ALTER TABLE mandanten ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutzer ENABLE ROW LEVEL SECURITY;
ALTER TABLE sitzungen ENABLE ROW LEVEL SECURITY;
ALTER TABLE einladungen ENABLE ROW LEVEL SECURITY;
ALTER TABLE passwort_resets ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mandanten_isolation_select ON mandanten;
DROP POLICY IF EXISTS mandanten_isolation_modify ON mandanten;
DROP POLICY IF EXISTS nutzer_isolation ON nutzer;
DROP POLICY IF EXISTS sitzungen_isolation ON sitzungen;
DROP POLICY IF EXISTS einladungen_isolation ON einladungen;
DROP POLICY IF EXISTS passwort_resets_isolation ON passwort_resets;
DROP POLICY IF EXISTS audit_isolation ON audit_events;

CREATE POLICY mandanten_isolation_select ON mandanten
    FOR SELECT USING (id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY mandanten_isolation_modify ON mandanten
    FOR ALL USING (id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY nutzer_isolation ON nutzer
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY sitzungen_isolation ON sitzungen
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY einladungen_isolation ON einladungen
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY passwort_resets_isolation ON passwort_resets
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY audit_isolation ON audit_events
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

-- Login/Reset brauchen den Nutzer anhand der E-Mail, bevor der Mandantenkontext
-- bekannt ist. SECURITY DEFINER umgeht RLS gezielt nur für diese eine Suche.
CREATE OR REPLACE FUNCTION auth_find_user_by_email(p_email TEXT)
RETURNS TABLE (
    id UUID, mandant_id UUID, name TEXT, email TEXT,
    password_hash TEXT, role TEXT, status TEXT
) LANGUAGE sql SECURITY DEFINER AS $$
    SELECT id, mandant_id, name, email, password_hash, role, status
    FROM nutzer WHERE email = p_email;
$$;

CREATE INDEX IF NOT EXISTS idx_nutzer_mandant ON nutzer(mandant_id);
CREATE INDEX IF NOT EXISTS idx_nutzer_email ON nutzer(email);
CREATE INDEX IF NOT EXISTS idx_sitzungen_nutzer ON sitzungen(nutzer_id);
CREATE INDEX IF NOT EXISTS idx_sitzungen_mandant ON sitzungen(mandant_id);
CREATE INDEX IF NOT EXISTS idx_einladungen_token ON einladungen(token);
CREATE INDEX IF NOT EXISTS idx_passwort_resets_token ON passwort_resets(token);
CREATE INDEX IF NOT EXISTS idx_login_versuche_email_ip ON login_versuche(email, ip, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_mandant ON audit_events(mandant_id, created_at);
