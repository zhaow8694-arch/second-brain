import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AtmosphericBackground } from "./components/AtmosphericBackground";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FateMatrices | Cyber Astrology & Energy Compass",
  description: "Decode your destiny matrix. Eastern Bazi meets futuristic energy mapping.",
  openGraph: {
    title: "FateMatrices - Decode Your Cyber Destiny",
    description: "Generate your Life Energy Fluctuation Chart. Eastern Bazi meets futuristic energy mapping.",
    url: "https://www.fatematrices.com",
    siteName: "FateMatrices",
    images: [
      {
        url: "/items/og-bazi.webp", 
        width: 1200,
        height: 630,
        alt: "FateMatrices Preview",
      },
    ],
    locale: "zh_CN",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "FateMatrices | Cyber Astrology",
    description: "Generate your Life Energy Fluctuation Chart now.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#030712] relative min-h-screen flex flex-col`}>
        <AtmosphericBackground />
        <div className="flex-1">
          {children}
        </div>
        <footer className="border-t border-gray-800/50 py-6 px-4 text-center">
          <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs uppercase tracking-wider font-mono">
            <a href="/terms" className="text-gray-500 hover:text-cyan-400 transition-colors">Terms</a>
            <a href="/privacy" className="text-gray-500 hover:text-cyan-400 transition-colors">Privacy</a>
            <a href="/refund" className="text-gray-500 hover:text-cyan-400 transition-colors">Refund</a>
            <a href="/disclaimer" className="text-gray-500 hover:text-cyan-400 transition-colors">Disclaimer</a>
            <a href="/contact" className="text-gray-500 hover:text-cyan-400 transition-colors">Contact</a>
          </div>
          <p className="text-gray-700 text-[10px] uppercase tracking-[0.3em] font-mono mt-3">FateMatrices © 2026</p>
        </footer>
      </body>
    </html>
  );
}