import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "FasalAI — Smart Agriculture for Pakistan 🌾",
  description:
    "AI-powered crop disease diagnosis, market predictions, weather alerts — built for Pakistani farmers",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body
        className={`${inter.className} min-h-screen bg-[#f0fdf4] text-gray-800 antialiased`}
      >
        {children}
      </body>
    </html>
  );
}