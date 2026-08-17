import { render, screen, waitFor } from "@testing-library/react";
import { VorgaengeTabelle } from "@/components/vorgaenge/vorgaenge-tabelle";
import { listVorgaenge } from "@/lib/api/vorgaenge";

jest.mock("@/lib/api/vorgaenge", () => ({
  listVorgaenge: jest.fn(),
}));

const mockedListVorgaenge = listVorgaenge as jest.Mock;

describe("VorgaengeTabelle", () => {
  afterEach(() => jest.clearAllMocks());

  it("zeigt geladene Vorgänge an", async () => {
    mockedListVorgaenge.mockResolvedValue({
      items: [
        {
          id: "1",
          status: "Neu",
          quelle: "Website",
          anliegen: "Heizung defekt",
          kunde_id: "k1",
          kunde_name: "Max Mustermann",
          objekt_id: null,
          objekt_adresse: null,
          zugewiesener_nutzer_id: null,
          created_at: "2026-08-17T10:00:00Z",
          updated_at: "2026-08-17T10:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });

    render(<VorgaengeTabelle rolle="Büro" />);

    await waitFor(() => expect(screen.getByText("Heizung defekt")).toBeInTheDocument());
    expect(screen.getByText("Max Mustermann")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Neuer Vorgang" })).toBeInTheDocument();
  });

  it("zeigt Leerzustand ohne Treffer", async () => {
    mockedListVorgaenge.mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 });

    render(<VorgaengeTabelle rolle="Monteur" />);

    await waitFor(() => expect(screen.getByText("Keine Vorgänge gefunden.")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: "Neuer Vorgang" })).not.toBeInTheDocument();
  });
});
