'use client';

import { SmoothScrollProvider } from '@/components/providers/smooth-scroll-provider';
import { Navbar } from './navbar';
import { HeroSection } from './hero-section';
import { FeaturesSection } from './features-section';
import { CTASection } from './cta-section';

export function LandingClient() {
  return (
    <SmoothScrollProvider>
      <Navbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <CTASection />
      </main>

      {/* Footer */}
      <footer className="py-8 border-t border-border/50 bg-background">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} AI Personal Trainer. Wszelkie prawa zastrzezone.
          </p>
        </div>
      </footer>
    </SmoothScrollProvider>
  );
}
