-- PROJ-23: Dedizierter Bildspeicher und WebP-Optimierung.
-- Erweitert die bestehende website_section_bild um Speicherort-Flag,
-- Content-Type und Anzeigename für neue WebP-Sektionsbilder. Bestehende
-- Zeilen bleiben Legacy (speicher_backend='legacy', unangetastet).

ALTER TABLE website_section_bild
    ADD COLUMN IF NOT EXISTS speicher_backend TEXT NOT NULL DEFAULT 'legacy'
        CHECK (speicher_backend IN ('legacy', 'website_images'));

ALTER TABLE website_section_bild
    ADD COLUMN IF NOT EXISTS content_type TEXT;

ALTER TABLE website_section_bild
    ADD COLUMN IF NOT EXISTS anzeigename TEXT;

-- Mandantenweit eindeutiger Anzeigename, nur für gesetzte Werte (Legacy-Zeilen
-- bleiben NULL und sind von der Eindeutigkeit ausgenommen).
CREATE UNIQUE INDEX IF NOT EXISTS idx_website_section_bild_anzeigename
    ON website_section_bild (mandant_id, anzeigename)
    WHERE anzeigename IS NOT NULL;
