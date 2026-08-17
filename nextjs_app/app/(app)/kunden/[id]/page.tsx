"use client";

import { useParams } from "next/navigation";
import { useAuth } from "@/app/providers";
import { KundeDetail } from "@/components/kunden/kunde-detail";
import type { Rolle } from "@/lib/theme/tokens";

export default function KundeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const rolle = (user?.rolle ?? "Büro") as Rolle;

  return <KundeDetail kundeId={id} rolle={rolle} />;
}
