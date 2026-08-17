import { Badge } from "@/components/ui/badge";
import type { VorgangStatus } from "@/lib/theme/tokens";

const VARIANTS: Record<VorgangStatus, "neutral" | "brand" | "success" | "warning" | "danger"> = {
  Neu: "brand",
  Rückruf: "warning",
  "Angebot offen": "warning",
  "Termin geplant": "neutral",
  Erledigt: "success",
  Abgeschlossen: "success",
};

export function VorgangStatusBadge({ status }: { status: VorgangStatus }) {
  return <Badge variant={VARIANTS[status] ?? "neutral"}>{status}</Badge>;
}
