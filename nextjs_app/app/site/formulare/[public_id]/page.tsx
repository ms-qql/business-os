"use client";

import { useParams } from "next/navigation";
import { OeffentlichesFormular } from "@/components/formulare/oeffentliches-formular";

export default function OeffentlichesFormularSeite() {
  const { public_id } = useParams<{ public_id: string }>();
  if (!public_id) return null;
  return <OeffentlichesFormular publicId={public_id} />;
}
