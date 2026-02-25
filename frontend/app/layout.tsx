import type { Metadata } from "next";
import { Outfit, Syne } from "next/font/google";
import "./globals.css";

// Primary body font - Technical, super clean
const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

// Distinctive, wide heading font - Neo-brutalist / clinical
const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Rural Health Triage",
  description: "Multilingual Symptom Checker & Triage",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${syne.variable} font-sans antialiased text-gray-900 bg-gray-50`}>
        {children}
      </body>
    </html>
  );
}
