'use client';

import { useRef, useEffect } from 'react';
import { Brain, Zap, Target, TrendingUp } from 'lucide-react';
import { gsap } from '@/lib/gsap-config';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const features = [
  {
    icon: Brain,
    title: 'Sztuczna Inteligencja',
    description:
      'Zaawansowane algorytmy AI analizuja Twoje cele i mozliwosci, tworzac optymalny plan treningowy.',
  },
  {
    icon: Target,
    title: 'Spersonalizowane Plany',
    description:
      'Kazdy plan jest dostosowany do Twoich indywidualnych potrzeb, wieku, wagi i poziomu zaawansowania.',
  },
  {
    icon: Zap,
    title: 'Szybkie Generowanie',
    description:
      'Twoj plan treningowy jest gotowy w kilka minut. Bez czekania, bez kompromisow.',
  },
  {
    icon: TrendingUp,
    title: 'Mierzalne Postepy',
    description:
      'Sledz swoje postepy i obserwuj, jak zbliżasz sie do swoich celow fitness.',
  },
];

export function FeaturesSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const cardsRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Title animation
      gsap.from(titleRef.current, {
        opacity: 0,
        y: 50,
        duration: 0.8,
        scrollTrigger: {
          trigger: titleRef.current,
          start: 'top 85%',
        },
      });

      // Staggered cards animation
      cardsRef.current.forEach((card, index) => {
        if (card) {
          gsap.from(card, {
            opacity: 0,
            y: 80,
            duration: 0.8,
            delay: index * 0.15,
            scrollTrigger: {
              trigger: card,
              start: 'top 85%',
            },
          });
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="features"
      className="py-24 md:py-32 bg-gradient-to-b from-background to-accent/5"
    >
      <div className="container mx-auto px-4">
        {/* Section Title */}
        <div className="text-center mb-16">
          <h2
            ref={titleRef}
            className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4"
          >
            Dlaczego{' '}
            <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              AI Personal Trainer
            </span>
            ?
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Poznaj funkcje, ktore uczynia Twoj trening bardziej efektywnym
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card
              key={feature.title}
              ref={(el) => { cardsRef.current[index] = el; }}
              className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 bg-card/50 backdrop-blur-sm border-border/50"
            >
              <CardHeader>
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
