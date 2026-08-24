-- PROJ-14: Branchenpaket-Konfiguration.
-- Erweitert nur die bestehende mandanten-Tabelle um drei nullable
-- Metadatenfelder, die beim einmaligen Onboarding-Übernahmevorgang
-- (POST /onboarding/branchenpaket-uebernehmen) geschrieben werden. Keine
-- neue Mandanten-Tabelle, keine weiteren Tabellen. Die Felder sind
-- mandantenbezogen und unterliegen bereits der bestehenden RLS-Policy auf
-- mandanten (id = current_setting('app.current_mandant_id')::uuid).

ALTER TABLE mandanten ADD COLUMN IF NOT EXISTS
    branchenpaket_kennung TEXT
        CHECK (branchenpaket_kennung IS NULL OR branchenpaket_kennung IN ('shk', 'entruempelung'));

ALTER TABLE mandanten ADD COLUMN IF NOT EXISTS
    branchenpaket_version INTEGER;

ALTER TABLE mandanten ADD COLUMN IF NOT EXISTS
    branchenpaket_uebernommen_am TIMESTAMPTZ;
