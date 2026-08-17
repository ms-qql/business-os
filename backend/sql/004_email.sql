-- PROJ-4: E-Mail-Inbox und Vorgangskommunikation.
-- Mandant-gescopete Postfach-, Thread-, Nachrichten- und Anhangstabellen.
-- Gleiches RLS-Muster wie 003_kunden_vorgaenge.sql (mandant_id-first-arg-Konvention,
-- set_config in db.py). Zugangsdaten im email_konto liegen verschlüsselt (Fernet),
-- nicht im Klartext.

CREATE TABLE IF NOT EXISTS email_konto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    imap_host TEXT NOT NULL,
    imap_port INTEGER NOT NULL DEFAULT 993,
    imap_user TEXT NOT NULL,
    imap_passwort TEXT NOT NULL,           -- Fernet-verschlüsselt
    imap_tls BOOLEAN NOT NULL DEFAULT TRUE,
    smtp_host TEXT NOT NULL,
    smtp_port INTEGER NOT NULL DEFAULT 465,
    smtp_user TEXT,                        -- NULL = gleiche Daten wie IMAP
    smtp_passwort TEXT,                    -- NULL = gleiche Daten wie IMAP
    smtp_tls BOOLEAN NOT NULL DEFAULT TRUE,
    letzter_abruf_status TEXT CHECK (letzter_abruf_status IN ('ok', 'fehler')),
    letzter_abruf_fehler_text TEXT,
    letzter_abruf_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Thread ist die Zuordnungseinheit: entweder an einen Vorgang gehängt oder
-- (während der Inbox-Triage) ohne Vorgang stehen gelassen. kunde_id ist
-- optional und dient der schnellen Anzeige bekannter Absender.
CREATE TABLE IF NOT EXISTS email_thread (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    vorgang_id UUID REFERENCES vorgang(id) ON DELETE SET NULL,
    kunde_id UUID REFERENCES kunde(id) ON DELETE SET NULL,
    betreff TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_nachricht (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    thread_id UUID NOT NULL REFERENCES email_thread(id) ON DELETE CASCADE,
    richtung TEXT NOT NULL CHECK (richtung IN ('eingehend', 'ausgehend')),
    absender TEXT NOT NULL,
    empfaenger TEXT NOT NULL,
    betreff TEXT,
    text_html TEXT,                        -- serverseitig bereinigt (bleach)
    text_plain TEXT,
    message_id TEXT,                       -- RFC Message-ID
    in_reply_to TEXT,                      -- RFC In-Reply-To
    referenzen TEXT,                       -- RFC References (Leerzeichen-getrennt)
    stabile_mail_kennung TEXT,             -- Message-ID als Dedup-Schlüssel
    gesendet_von_nutzer_id UUID REFERENCES nutzer(id) ON DELETE SET NULL,
    empfangen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_anhang (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandant_id UUID NOT NULL REFERENCES mandanten(id) ON DELETE CASCADE,
    nachricht_id UUID NOT NULL REFERENCES email_nachricht(id) ON DELETE CASCADE,
    dateiname TEXT NOT NULL,
    objektpfad TEXT NOT NULL,
    content_type TEXT NOT NULL,
    groesse_bytes INTEGER NOT NULL,
    verarbeitet BOOLEAN NOT NULL DEFAULT TRUE,   -- FALSE = "Anhang konnte nicht verarbeitet werden"
    fehler_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE email_konto ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_thread ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_nachricht ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_anhang ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS email_konto_isolation ON email_konto;
DROP POLICY IF EXISTS email_thread_isolation ON email_thread;
DROP POLICY IF EXISTS email_nachricht_isolation ON email_nachricht;
DROP POLICY IF EXISTS email_anhang_isolation ON email_anhang;

CREATE POLICY email_konto_isolation ON email_konto
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY email_thread_isolation ON email_thread
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY email_nachricht_isolation ON email_nachricht
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);
CREATE POLICY email_anhang_isolation ON email_anhang
    FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid);

CREATE INDEX IF NOT EXISTS idx_email_konto_mandant ON email_konto(mandant_id);
CREATE INDEX IF NOT EXISTS idx_email_thread_mandant ON email_thread(mandant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_email_thread_vorgang ON email_thread(mandant_id, vorgang_id);
CREATE INDEX IF NOT EXISTS idx_email_thread_kunde ON email_thread(mandant_id, kunde_id);
CREATE INDEX IF NOT EXISTS idx_email_nachricht_thread ON email_nachricht(mandant_id, thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_email_nachricht_message_id ON email_nachricht(mandant_id, message_id);
CREATE INDEX IF NOT EXISTS idx_email_anhang_nachricht ON email_anhang(mandant_id, nachricht_id);

-- Dedup gegen doppelt abgeholte Nachrichten: stabile Mail-Kennung (Message-ID)
-- pro Mandant eindeutig. Teilindex, damit ausgehende Mails ohne Kennung nicht
-- gegen die Unique-Regel verstoßen.
CREATE UNIQUE INDEX IF NOT EXISTS uq_email_nachricht_kennung
    ON email_nachricht(mandant_id, stabile_mail_kennung)
    WHERE stabile_mail_kennung IS NOT NULL;
