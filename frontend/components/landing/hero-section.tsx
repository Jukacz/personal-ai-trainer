'use client';

import { useRef, useEffect } from 'react';
import Link from 'next/link';
import { ChevronDown, Dumbbell, Activity, Target, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { gsap, ScrollTrigger } from '@/lib/gsap-config';

export function HeroSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const floatingContainerRef = useRef<HTMLDivElement>(null);
  const gradientRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Initial entrance animations
      const tl = gsap.timeline();

      tl.from(titleRef.current, {
        opacity: 0,
        y: 80,
        duration: 1,
        ease: 'power3.out',
      })
        .from(
          subtitleRef.current,
          {
            opacity: 0,
            y: 40,
            duration: 0.8,
            ease: 'power3.out',
          },
          '-=0.6'
        )
        .from(
          ctaRef.current,
          {
            opacity: 0,
            y: 30,
            duration: 0.6,
            ease: 'power3.out',
          },
          '-=0.4'
        )
        .from(
          '.floating-icon',
          {
            opacity: 0,
            scale: 0.5,
            duration: 0.8,
            stagger: 0.1,
            ease: 'back.out(1.7)',
          },
          '-=0.4'
        );

      // Floating icons continuous animation
      gsap.utils.toArray<HTMLElement>('.floating-icon').forEach((el, index) => {
        gsap.to(el, {
          y: '+=25',
          duration: 2.5 + index * 0.3,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        });
        gsap.to(el, {
          x: '+=15',
          duration: 3 + index * 0.4,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
          delay: index * 0.2,
        });
      });

      // Gradient animation
      if (gradientRef.current) {
        gsap.to(gradientRef.current, {
          backgroundPosition: '200% 50%',
          duration: 10,
          repeat: -1,
          ease: 'none',
        });
      }

      // Scroll-based parallax (content wrapper moves up with parallax)
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: 'bottom top',
        scrub: 0.5,
        onUpdate: (self) => {
          const progress = self.progress;

          // Title parallax
          gsap.set(titleRef.current, {
            y: progress * -80,
            opacity: 1 - progress * 1.5,
          });

          // Subtitle parallax (moves faster)
          gsap.set(subtitleRef.current, {
            y: progress * -60,
            opacity: 1 - progress * 2,
          });

          // CTA parallax
          gsap.set(ctaRef.current, {
            y: progress * -40,
            opacity: 1 - progress * 2.5,
          });

          // Floating container parallax
          if (floatingContainerRef.current) {
            gsap.set(floatingContainerRef.current, {
              y: progress * -100,
              opacity: 1 - progress * 1.2,
            });
          }
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
    >
      {/* Animated Gradient Background */}
      <div
        ref={gradientRef}
        className="absolute inset-0 z-0"
        style={{
          background:
            'linear-gradient(135deg, hsl(var(--primary) / 0.15) 0%, hsl(var(--background)) 25%, hsl(var(--background)) 50%, hsl(var(--primary) / 0.1) 75%, hsl(var(--primary) / 0.2) 100%)',
          backgroundSize: '200% 200%',
          backgroundPosition: '0% 50%',
        }}
      />

      {/* Floating Elements Container */}
      <div ref={floatingContainerRef} className="absolute inset-0 z-10 pointer-events-none">
        <div className="floating-icon absolute top-1/4 left-[10%] opacity-20 dark:opacity-30">
          <Dumbbell className="h-20 w-20 text-primary" />
        </div>
        <div className="floating-icon absolute top-1/3 right-[15%] opacity-20 dark:opacity-30">
          <Activity className="h-24 w-24 text-primary" />
        </div>
        <div className="floating-icon absolute bottom-1/3 left-[15%] opacity-15 dark:opacity-25">
          <Target className="h-16 w-16 text-primary" />
        </div>
        <div className="floating-icon absolute bottom-1/4 right-[12%] opacity-15 dark:opacity-25">
          <Zap className="h-20 w-20 text-primary" />
        </div>
      </div>

      {/* Radial Gradient Overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,hsl(var(--background))_100%)] z-10 pointer-events-none" />

      {/* Content */}
      <div className="container mx-auto px-4 relative z-20 text-center pt-20">
        <h1
          ref={titleRef}
          className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold mb-6 leading-tight"
        >
          <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
            AI Personal
          </span>
          <br />
          <span className="text-foreground">Trainer</span>
        </h1>

        <p
          ref={subtitleRef}
          className="text-lg sm:text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto mb-8"
        >
          Twoj inteligentny asystent treningowy. Spersonalizowane plany treningowe
          generowane przez sztuczna inteligencje.
        </p>

        <div ref={ctaRef} className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild size="lg" className="text-lg h-14 px-8">
            <Link href="/dashboard">Rozpocznij za darmo</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="text-lg h-14 px-8">
            <Link href="#features">Dowiedz sie wiecej</Link>
          </Button>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 animate-bounce">
        <ChevronDown className="h-8 w-8 text-muted-foreground" />
      </div>
    </section>
  );
}
