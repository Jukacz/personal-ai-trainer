import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { RootProviders } from "@/components/providers/root-providers";
import { ThemeToggle } from "@/components/theme-toggle";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  title: {
    default: 'AI Personal Trainer',
    template: '%s | AI Personal Trainer',
  },
  description: 'Twoj inteligentny asystent treningowy - generuj spersonalizowane plany treningowe',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <RootProviders>
          <ThemeToggle />
          {children}
        </RootProviders>
      </body>
    </html>
  );
}
