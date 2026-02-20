import type { Metadata } from 'next';
import { LandingClient } from '@/components/landing/landing-client';

export const metadata: Metadata = {
  title: 'AI Personal Trainer - Spersonalizowane Plany Treningowe',
  description:
    'Wygeneruj spersonalizowany plan treningowy za pomoca sztucznej inteligencji. Dostosowany do Twoich celow, wieku i poziomu zaawansowania. Zacznij juz dzis za darmo!',
  keywords: [
    'trener personalny',
    'plan treningowy',
    'fitness',
    'AI',
    'cwiczenia',
    'silownia',
    'trening',
    'odchudzanie',
    'budowanie miesni',
  ],
  authors: [{ name: 'AI Personal Trainer' }],
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    url: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
    siteName: 'AI Personal Trainer',
    title: 'AI Personal Trainer - Spersonalizowane Plany Treningowe',
    description:
      'Wygeneruj spersonalizowany plan treningowy za pomoca AI. Dostosowany do Twoich celow i mozliwosci.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'AI Personal Trainer',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AI Personal Trainer - Spersonalizowane Plany Treningowe',
    description:
      'Wygeneruj spersonalizowany plan treningowy za pomoca AI. Zacznij za darmo!',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

// Structured Data (JSON-LD)
const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'AI Personal Trainer',
  applicationCategory: 'HealthApplication',
  operatingSystem: 'Web',
  description:
    'Aplikacja do generowania spersonalizowanych planow treningowych za pomoca sztucznej inteligencji.',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'PLN',
  },
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.9',
    ratingCount: '500',
  },
};

export default function HomePage() {
  return (
    <>
      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <LandingClient />
    </>
  );
}
