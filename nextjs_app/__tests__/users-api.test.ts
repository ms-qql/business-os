import { inviteNutzer } from "@/lib/api/users";

describe("inviteNutzer", () => {
  it("übersetzt die UI-Rolle in das API-Schema", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 201,
      text: async () => JSON.stringify({}),
    });

    await inviteNutzer({ name: "Büro", email: "buero@betrieb.de", rolle: "Büro" });

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/users",
      expect.objectContaining({
        body: JSON.stringify({ name: "Büro", email: "buero@betrieb.de", role: "Buero" }),
      }),
    );
  });
});
