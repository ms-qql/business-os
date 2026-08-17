import { render, screen } from "@testing-library/react";
import { VorgangStatusBadge } from "@/components/vorgaenge/vorgang-status-badge";

describe("VorgangStatusBadge", () => {
  it.each([
    "Neu",
    "Rückruf",
    "Angebot offen",
    "Termin geplant",
    "Erledigt",
    "Abgeschlossen",
  ] as const)("zeigt den Status %s an", (status) => {
    render(<VorgangStatusBadge status={status} />);
    expect(screen.getByText(status)).toBeInTheDocument();
  });
});
