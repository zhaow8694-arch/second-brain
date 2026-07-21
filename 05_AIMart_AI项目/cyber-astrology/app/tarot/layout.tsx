import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Western Arcana | FateMatrices",
  description: "Tarot · Subconscious Decode · Quantum Oracle",
  openGraph: {
    title: "Western Arcana - Cyber Tarot Reading",
    description: "Access your digital oracle and subconsciously mapped fate.",
    images: ["/items/og-tarot.webp"],
  },
};

export default function TarotLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
