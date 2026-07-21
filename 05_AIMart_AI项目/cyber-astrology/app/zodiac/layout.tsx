import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Zodiac Nebula | FateMatrices",
  description: "Horoscope · MBTI Synergy · Love Match",
  openGraph: {
    title: "Zodiac Nebula - Interstellar Pathfinding",
    description: "Align your star chart with MBTI personality matrices.",
    images: ["/items/og-zodiac.webp"],
  },
};

export default function ZodiacLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
