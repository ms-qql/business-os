import { updateFeld } from "@/lib/api/formulare";

describe("updateFeld", () => {
  it("sends options only for selection fields", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ id: "form-1", name: "Test", komplexitaet: "einfach", draft_revision: 2, veroeffentlicht: false, schritte: [] }),
    });

    await updateFeld("form-1", "step-1", "field-1", { label: "Foto", pflichtfeld: true }, 1);

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/formulare/form-1/schritte/step-1/felder/field-1",
      expect.objectContaining({ body: JSON.stringify({ label: "Foto", pflichtfeld: true, draft_revision: 1 }) }),
    );
  });
});
