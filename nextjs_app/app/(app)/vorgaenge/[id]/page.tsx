"use client";

import { useParams } from "next/navigation";
import { useAuth } from "@/app/providers";
import { VorgangDetail } from "@/components/vorgaenge/vorgang-detail";
import type { Rolle } from "@/lib/theme/tokens";

export default function VorgangDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const rolle = (user?.rolle ?? "Büro") as Rolle;

  return <VorgangDetail vorgangId={id} rolle={rolle} />;
}
