# Handoff: PROJ-12 Website-Baukasten — Bild-Upload/Look&Feel

Datum: 2026-08-23 · Feature: `features/PROJ-12-freier-website-baukasten-und-landingpage.md` (Status: Deployed)

## Ausgangsmeldung (Nutzer)
- Bild-Upload im Sektion-Editor ("Landingpage gestalten") funktioniert nicht
- Drag&Drop funktioniert nicht
- Look-and-Feel der Landingpage entspricht nicht dem Zieldesign
- Frage: braucht Bild-Upload Redeploy?

## Diagnose (durchgeführt)
Browser-Console + Backend-Logs vom Nutzer ausgewertet:
- Upload-Request selbst lief durch (`POST /website-builder/sections/{id}/bild` → 200 OK)
- Bild lud danach aber nicht: `net::ERR_SSL_PROTOCOL_ERROR` auf
  `crm.erol.msce.info:9000/business-os/website-sections/.../*.png?X-Amz-...` — eine
  **rohe MinIO-Presigned-URL auf Port 9000**, nicht die geplante proxied App-HTTPS-URL.

**Root Cause gefunden:** `backend/app/features/website/builder_service.py:56`
(`_public_bild()`, Rückgabepfad für `get_builder_state()` → Upload/Patch/Delete-Response
im **Editor**) gab weiterhin `storage_mod.storage.presigned_get_url(...)` zurück.
Ein früherer Fix (Commit 9645d3d, "Serve section images through app HTTPS") hatte nur
`public_sections()` (Zeile 252, öffentliche Landingpage `/public/site`) korrigiert —
der Editor-Pfad blieb kaputt.

Zweiter, separater Befund (kein Bug): 404en auf `leistungen/energie`,
`leistungen/heizung` etc. in der Console sind reines Next.js-RSC-Prefetch-Rauschen —
Routen (`nextjs_app/app/site/leistungen/[slug]/page.tsx`) existieren und sind korrekt
verdrahtet.

## Fix (angewendet + committed + deployed)
- `_public_bild()` liefert jetzt `f"/public/sections/{section['id']}/bild"` statt der
  presigned MinIO-URL — gleiches Muster wie der bereits funktionierende Pfad.
- Bestehender Test `test_upload_and_delete_section_bild` hatte den Bug bisher
  **explizit als Soll-Verhalten** einprogrammiert (`assert ...startswith("memory://")`,
  die Storage-Test-Double-URL) — deshalb wurde der Bug nie von der Testsuite gefangen.
  Assertion korrigiert auf die proxied URL.
- Backend-Testsuite komplett grün (`conda run -n Dashboard --no-capture-output python -m pytest backend/`), keine Regression.
- QA-Ergebnis dokumentiert in der Feature-Spec, Abschnitt "Nachtest Bugfix
  2026-08-23 — Bild-URL im Editor".

### Commits (main)
- `98caf4f` — fix(PROJ-12): Serve section image via app HTTPS in builder editor response
- `d3427d5` — deploy(PROJ-12): Mark section-image URL fix deployed (Bump 0.1.10)
- Tag: `v0.1.10-PROJ-12`, gepusht nach `origin/main` → Dokploy Auto-Deploy ausgelöst

## Offen / nicht abgeschlossen
**Nutzer meldet: "das hat nicht funktioniert"** — nach Push/Deploy nicht mehr im Detail
verifiziert, WAS genau noch nicht geht. Mögliche Ursachen, noch nicht geprüft:
1. Deploy-Build auf Dokploy selbst fehlgeschlagen (Logs nicht eingesehen)
2. Fix behebt nur die geloggte SSL-Fehlermeldung — Bild-Upload/Drag&Drop-UI-Handler
   selbst (`nextjs_app/components/website-builder/section-editor.tsx`) waren beim
   ersten Explore-Pass als strukturell korrekt eingestuft (Handler, FormData,
   Drag&Drop-Events vorhanden) — aber NICHT im Browser live nachgetestet
   (kein Browser-Tool in der Session verfügbar)
3. Service-Worker-/Browser-Cache nicht hart neu geladen nach Deploy
4. Look-and-Feel-Thema (`nextjs_app/app/globals.css` CSS-Variablen) komplett unangetastet
   — falls das gemeint ist, ist dafür noch gar kein Fix erfolgt
5. Ggf. neuer/anderer Fehler nach dem Fix (noch nicht diagnostiziert)

## Nächste Schritte für die neue Session
1. Nutzer nach konkretem aktuellem Fehlerbild fragen: Screenshot + Browser-Console
   + Netzwerk-Tab-Status-Code beim Upload-Versuch (wie beim letzten Mal sehr hilfreich)
2. Dokploy-Deployments-Logs für Build nach `d3427d5`/Tag `v0.1.10-PROJ-12` prüfen —
   ist der Build überhaupt grün durchgelaufen?
3. Falls Build grün: `/api/health` + hard-refresh (Strg/Cmd+Shift+R) prüfen, dann
   Upload erneut testen
4. Falls weiterhin `ERR_SSL_PROTOCOL_ERROR` oder ähnlich: prüfen, ob evtl. weitere
   Code-Pfade (außerhalb `builder_service.py`) noch presigned MinIO-URLs zurückgeben —
   projektweit nach `presigned_get_url(` grep
5. Look-and-Feel-Thema separat behandeln (eigenes Problem, noch nicht angefasst) —
   `nextjs_app/app/globals.css` Farb-/Radius-Tokens gegen Zieldesign abgleichen
6. Bild-Format-Optimierung (WebP-Konvertierung) ist vom Nutzer explizit als
   **späteres Feature** eingestuft, nicht Teil dieses Bugfixes — für `/abc-requirements`
   vormerken
