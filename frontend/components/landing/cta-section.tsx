'use client';

import { useRef, useEffect } from 'react';
import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { gsap } from '@/lib/gsap-config';

export function CTASection() {
  const sectionRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Parallax background effect
      gsap.to(sectionRef.current, {
        backgroundPosition: '50% 30%',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 1,
        },
      });

      // Content fade in - triggers later (when section is 50% visible)
      gsap.from(contentRef.current, {
        opacity: 0,
        y: 60,
        scale: 0.95,
        duration: 1.2,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 50%',
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="about"
      className="relative py-24 md:py-32 overflow-hidden"
      style={{
        backgroundImage:
          'radial-gradient(ellipse at center, hsl(var(--primary) / 0.15) 0%, transparent 70%)',
        backgroundPosition: '50% 50%',
        backgroundSize: '200% 200%',
      }}
    >
      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div
          ref={contentRef}
          className="max-w-3xl mx-auto text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-8">
            <Sparkles className="h-4 w-4" />
            <span className="text-sm font-medium">Darmowy dostep</span>
          </div>

          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
            Zacznij swoja
            <br />
            <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
              przygode z fitnessem
            </span>
          </h2>

          <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-xl mx-auto">
            Dolacz do tysiecy osob, ktore juz korzystaja z AI Personal Trainer.
            Wygeneruj swoj pierwszy plan treningowy juz dzis!
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" className="text-lg h-14 px-8 group">
              <Link href="/dashboard">
                Utworz plan treningowy
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
            <Button
              asChild
              variant="ghost"
              size="lg"
              className="text-lg h-14 px-8"
            >
              <Link href="/register">Zaloz konto</Link>
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 mt-16 pt-16 border-t border-border/50">
            <div>
              <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                1000+
              </div>
              <div className="text-sm text-muted-foreground">
                Wygenerowanych planow
              </div>
            </div>
            <div>
              <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                500+
              </div>
              <div className="text-sm text-muted-foreground">
                Aktywnych uzytkownikow
              </div>
            </div>
            <div>
              <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                4.9
              </div>
              <div className="text-sm text-muted-foreground">
                Srednia ocena
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
