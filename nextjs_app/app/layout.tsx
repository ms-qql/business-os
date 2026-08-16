import type { Metadata } from "next";
import { AuthProvider } from "@/app/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Business OS",
  description: "Mandanten, Anmeldung und Rollen",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
