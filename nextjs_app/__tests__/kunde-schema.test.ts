import { kundeSchema } from "@/lib/schemas/kunde";

describe("kundeSchema", () => {
  it("verlangt E-Mail oder Telefon", () => {
    const res = kundeSchema.safeParse({ name: "Max Mustermann", email: "", telefon: "" });
    expect(res.success).toBe(false);
  });

  it("akzeptiert Name + Telefon ohne E-Mail", () => {
    const res = kundeSchema.safeParse({ name: "Max Mustermann", email: "", telefon: "0170123456" });
    expect(res.success).toBe(true);
  });

  it("lehnt ungültige E-Mail ab", () => {
    const res = kundeSchema.safeParse({ name: "Max Mustermann", email: "keine-email", telefon: "" });
    expect(res.success).toBe(false);
  });
});
