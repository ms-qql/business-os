import { positionSchema, freigabeSchema } from "@/lib/schemas/angebot";

const basis = {
  bezeichnung: "Montage",
  menge: 1,
  einheit: "Stück",
  einzelpreis: 100,
  steuersatz: 19,
};

describe("positionSchema — Rabatt-Umschalter-Validierung", () => {
  it("akzeptiert gültigen Prozent-Rabatt", () => {
    const res = positionSchema.safeParse({ ...basis, rabatt_typ: "prozent", rabatt_wert: 10 });
    expect(res.success).toBe(true);
  });

  it("lehnt Prozent-Rabatt über 100 ab", () => {
    const res = positionSchema.safeParse({ ...basis, rabatt_typ: "prozent", rabatt_wert: 150 });
    expect(res.success).toBe(false);
  });

  it("akzeptiert gültigen Euro-Rabatt", () => {
    const res = positionSchema.safeParse({ ...basis, rabatt_typ: "betrag", rabatt_wert: 50 });
    expect(res.success).toBe(true);
  });

  it("lehnt Euro-Rabatt ab, der die Positionssumme unter 0 senkt", () => {
    const res = positionSchema.safeParse({ ...basis, rabatt_typ: "betrag", rabatt_wert: 200 });
    expect(res.success).toBe(false);
  });

  it("lehnt fehlende Bezeichnung ab", () => {
    const res = positionSchema.safeParse({ ...basis, bezeichnung: "", rabatt_typ: "prozent", rabatt_wert: 0 });
    expect(res.success).toBe(false);
  });
});

describe("freigabeSchema", () => {
  it("verlangt gültige E-Mail und Betreff", () => {
    expect(freigabeSchema.safeParse({ empfaenger: "kunde@beispiel.de", betreff: "Ihr Angebot" }).success).toBe(true);
    expect(freigabeSchema.safeParse({ empfaenger: "keine-email", betreff: "Ihr Angebot" }).success).toBe(false);
    expect(freigabeSchema.safeParse({ empfaenger: "kunde@beispiel.de", betreff: "" }).success).toBe(false);
  });
});
