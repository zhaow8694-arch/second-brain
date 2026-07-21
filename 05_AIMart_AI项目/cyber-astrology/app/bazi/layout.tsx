import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Eastern Matrix | FateMatrices",
  description: "Bazi · Wealth Pillars · Life Energy Mapping",
  openGraph: {
    title: "Eastern Matrix - Decode Your Bazi Destiny",
    description: "Quantum resonance alignment for your Five Elements matrix.",
    images: ["/items/og-bazi.webp"],
  },
};

export default function BaziLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
