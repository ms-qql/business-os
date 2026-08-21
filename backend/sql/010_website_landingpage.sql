-- PROJ-12: Freier Website-Baukasten und Landingpage.
-- Drei neue Tabellen (website_landingpage, website_section, website_section_bild)
-- mit mandant_id, Fremdschlüsseln, RLS und Lesereihenfolge-Index. Kein Alembic;
-- folgt der Roh-SQL-Konvention von 001–009 (IF NOT EXISTS / DROP POLICY IF EXISTS).

CREATE TABLE IF NOT EXISTS website_landingpage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL UNIQUE REFERENCES mandanten(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS website_section (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    landingpage_id UUID NOT NULL REFERENCES website_landingpage(id) ON DELETE CASCADE,
    typ TEXT NOT NULL CHECK (typ IN (
        'hero', 'text_mit_bild', 'leistungen', 'kennzahlen', 'ablauf', 'faq', 'kontakt', 'cta'
    )),
    visible BOOLEAN NOT NULL DEFAULT TRUE,
    position INTEGER NOT NULL,
    inhalt JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mandant_id, landingpage_id, position)
);

CREATE TABLE IF NOT EXISTS website_section_bild (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    section_id UUID NOT NULL UNIQUE REFERENCES website_section(id) ON DELETE CASCADE,
    objektpfad TEXT NOT NULL,
    alt_text TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE website_landingpage ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_section ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_section_bild ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS website_landingpage_isolation ON website_landingpage;
DROP POLICY IF EXISTS website_section_isolation ON website_section;
DROP POLICY IF EXISTS website_section_bild_isolation ON website_section_bild;

CREATE POLICY website_landingpage_isolation ON website_landingpage
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY website_section_isolation ON website_section
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE POLICY website_section_bild_isolation ON website_section_bild
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

-- Lesereihenfolge: sortierte Sektionen je Landingpage.
CREATE INDEX IF NOT EXISTS idx_website_section_lp_pos
    ON website_section(landingpage_id, position);
CREATE INDEX IF NOT EXISTS idx_website_section_mandant
    ON website_section(mandant_id, landingpage_id);
CREATE INDEX IF NOT EXISTS idx_website_section_bild_section
    ON website_section_bild(section_id);
