-- Bereits gespeicherte Website-Anfragen in sichtbare Vorgänge übernehmen.
-- Idempotent: Nur noch nicht verknüpfte Anfragen werden verarbeitet.
DO $$
DECLARE
    anfrage_record RECORD;
    kunde_id UUID;
    objekt_id UUID;
    neuer_vorgang_id UUID;
BEGIN
    FOR anfrage_record IN
        SELECT * FROM anfrage WHERE vorgang_id IS NULL
    LOOP
        kunde_id := gen_random_uuid();
        INSERT INTO kunde (id, mandant_id, name, email, telefon)
        VALUES (kunde_id, anfrage_record.mandant_id, anfrage_record.name,
                anfrage_record.email, anfrage_record.telefon);

        objekt_id := gen_random_uuid();
        INSERT INTO objekt (id, mandant_id, kunde_id, adresse)
        VALUES (objekt_id, anfrage_record.mandant_id, kunde_id, anfrage_record.adresse);

        neuer_vorgang_id := gen_random_uuid();
        INSERT INTO vorgang (id, mandant_id, kunde_id, objekt_id, status, quelle, anliegen, notizen,
                             created_at, updated_at)
        VALUES (neuer_vorgang_id, anfrage_record.mandant_id, kunde_id, objekt_id, 'Neu',
                anfrage_record.quelle, anfrage_record.anliegen,
                concat_ws(' | ', 'Dringlichkeit: ' || anfrage_record.dringlichkeit,
                          CASE WHEN anfrage_record.zeitfenster IS NOT NULL
                               THEN 'Zeitfenster: ' || anfrage_record.zeitfenster END),
                anfrage_record.created_at, anfrage_record.created_at);

        INSERT INTO vorgang_historie (id, mandant_id, vorgang_id, ereignis, detail, created_at)
        VALUES (gen_random_uuid(), anfrage_record.mandant_id, neuer_vorgang_id, 'angelegt',
                'Aus Website-Anfrage übernommen (' || anfrage_record.id || ')', anfrage_record.created_at);

        INSERT INTO vorgang_dokument (id, mandant_id, vorgang_id, dateiname, objektpfad,
                                      content_type, groesse_bytes, created_at)
        SELECT gen_random_uuid(), mandant_id, neuer_vorgang_id, dateiname, objektpfad,
               CASE
                   WHEN lower(dateiname) LIKE '%.jpg' OR lower(dateiname) LIKE '%.jpeg' THEN 'image/jpeg'
                   WHEN lower(dateiname) LIKE '%.png' THEN 'image/png'
                   WHEN lower(dateiname) LIKE '%.gif' THEN 'image/gif'
                   WHEN lower(dateiname) LIKE '%.webp' THEN 'image/webp'
                   WHEN lower(dateiname) LIKE '%.pdf' THEN 'application/pdf'
                   ELSE 'application/octet-stream'
               END,
               0, created_at
        FROM anfragebild
        WHERE anfrage_id = anfrage_record.id;

        UPDATE anfrage SET vorgang_id = neuer_vorgang_id WHERE id = anfrage_record.id;
    END LOOP;
END $$;
