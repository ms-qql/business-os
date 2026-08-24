import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SectionEditor } from "@/components/website-builder/section-editor";
import { uploadSectionBild } from "@/lib/api/website-builder";
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

it("zeigt den Anzeigenamen eines Sektionsbilds", () => {
  const withImage = {
    ...section(inhalte[0]),
    bild: { url: "/public/sections/hero/bild", alt_text: "Dach", anzeigename: "Hero – Dach" },
  };
  render(
    <SectionEditor
      section={withImage}
      version={1}
      onSaveInhalt={jest.fn().mockResolvedValue(undefined)}
      onStateUpdate={jest.fn()}
    />,
  );
  expect(screen.getByText("Hero – Dach")).toBeInTheDocument();
});

it("speichert ungesicherten Inhalt vor dem Bild-Upload", async () => {
  const original = { typ: "hero" as const, titel: "Alt", text: "Alter Text" };
  const changed = { ...original, titel: "Neu", text: "Neuer Text" };
  const saved = { landingpage_id: "lp", version: 2, sections: [section(changed)] };
  const uploaded = {
    landingpage_id: "lp",
    version: 3,
    sections: [{ ...section(changed), bild: { url: "/bild", alt_text: "", anzeigename: null } }],
  };
  const onSaveInhalt = jest.fn().mockResolvedValue(saved);
  (uploadSectionBild as jest.Mock).mockResolvedValue(uploaded);
  const { container } = render(
    <SectionEditor section={section(original)} version={1} onSaveInhalt={onSaveInhalt} onStateUpdate={jest.fn()} />,
  );

  fireEvent.change(screen.getByDisplayValue("Alt"), { target: { value: "Neu" } });
  fireEvent.change(screen.getByDisplayValue("Alter Text"), { target: { value: "Neuer Text" } });
  fireEvent.change(container.querySelector('input[type="file"]')!, {
    target: { files: [new File(["bild"], "bild.png", { type: "image/png" })] },
  });

  await waitFor(() => expect(onSaveInhalt).toHaveBeenCalledWith(changed, true));
  expect(uploadSectionBild).toHaveBeenCalledWith("hero", expect.any(File), "", 2);
});
