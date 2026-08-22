import { render, screen } from "@testing-library/react";
import { SectionEditor } from "@/components/website-builder/section-editor";
import type { SektionInhaltUnion, WebsiteSection } from "@/lib/website-builder-types";

jest.mock("@/lib/api/website-builder", () => ({
  deleteSectionBild: jest.fn(),
  isConflict: jest.fn(),
  uploadSectionBild: jest.fn(),
}));

const inhalte: SektionInhaltUnion[] = [
  { typ: "hero", titel: "Hero", text: "" },
  { typ: "text_mit_bild", titel: "Text", text: "" },
  { typ: "leistungen", titel: "Leistungen", einleitung: "" },
  { typ: "kennzahlen", titel: "Kennzahlen", kennzahlen: [] },
  { typ: "ablauf", titel: "Ablauf", schritte: [] },
  { typ: "faq", titel: "FAQ", fragen: [] },
  { typ: "kontakt", titel: "Kontakt", einleitung: "" },
  { typ: "cta", titel: "CTA", text: "" },
];

function section(inhalt: SektionInhaltUnion): WebsiteSection {
  return { id: inhalt.typ, typ: inhalt.typ, visible: true, position: 1, inhalt, bild: null };
}

it("übernimmt beim Wechsel den Inhalt jedes Sektionstyps", () => {
  const props = {
    version: 1,
    onSaveInhalt: jest.fn().mockResolvedValue(undefined),
    onStateUpdate: jest.fn(),
  };
  const view = render(<SectionEditor key={inhalte[0].typ} section={section(inhalte[0])} {...props} />);

  for (const inhalt of inhalte.slice(1)) {
    view.rerender(<SectionEditor key={inhalt.typ} section={section(inhalt)} {...props} />);
    expect(screen.getByDisplayValue(inhalt.titel)).toBeInTheDocument();
  }
});
