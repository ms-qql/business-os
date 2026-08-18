import { positionsSumme, summenBerechnen, rabattFehler, type Position } from "@/lib/angebot-berechnung";

describe("positionsSumme", () => {
  it("berechnet Prozent-Rabatt", () => {
    // 10 Std. * 50 € = 500, 10 % Rabatt -> 450
    expect(positionsSumme({ menge: 10, einzelpreis: 50, rabatt_typ: "prozent", rabatt_wert: 10 })).toBe(450);
  });

  it("berechnet Euro-Rabatt", () => {
    expect(positionsSumme({ menge: 2, einzelpreis: 100, rabatt_typ: "betrag", rabatt_wert: 50 })).toBe(150);
  });

  it("rundet auf 2 Nachkommastellen", () => {
    expect(positionsSumme({ menge: 3, einzelpreis: 10.005, rabatt_typ: "prozent", rabatt_wert: 0 })).toBe(30.02);
  });

  it("lässt die Positionssumme nie negativ werden", () => {
    expect(positionsSumme({ menge: 1, einzelpreis: 10, rabatt_typ: "betrag", rabatt_wert: 50 })).toBe(0);
  });
});

describe("summenBerechnen", () => {
  it("summiert Netto/Steuer/Brutto über mehrere Positionen mit unterschiedlichen Steuersätzen", () => {
    const positionen: Position[] = [
      { menge: 1, einzelpreis: 100, steuersatz: 19, rabatt_typ: "prozent", rabatt_wert: 0 },
      { menge: 1, einzelpreis: 100, steuersatz: 7, rabatt_typ: "betrag", rabatt_wert: 20 },
    ];
    const summen = summenBerechnen(positionen);
    expect(summen.netto).toBe(180); // 100 + 80
    expect(summen.steuer).toBe(24.6); // 19 + 5.6
    expect(summen.brutto).toBe(204.6);
  });

  it("liefert 0/0/0 ohne Positionen", () => {
    expect(summenBerechnen([])).toEqual({ netto: 0, steuer: 0, brutto: 0 });
  });
});

describe("rabattFehler", () => {
  it("lehnt Prozent außerhalb 0-100 ab", () => {
    expect(rabattFehler("prozent", 101, 1, 100)).toMatch(/zwischen 0 und 100/);
    expect(rabattFehler("prozent", -1, 1, 100)).toMatch(/zwischen 0 und 100/);
    expect(rabattFehler("prozent", 50, 1, 100)).toBeNull();
  });

  it("lehnt negativen Euro-Rabatt ab", () => {
    expect(rabattFehler("betrag", -5, 1, 100)).toMatch(/nicht negativ/);
  });

  it("lehnt Euro-Rabatt ab, der die Positionssumme unter 0 senkt", () => {
    expect(rabattFehler("betrag", 150, 1, 100)).toMatch(/nicht unter 0/);
    expect(rabattFehler("betrag", 100, 1, 100)).toBeNull();
  });
});
