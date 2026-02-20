'use client';

import { useEffect, useRef, createContext, useContext, ReactNode } from 'react';
import Lenis from 'lenis';
import { gsap, ScrollTrigger } from '@/lib/gsap-config';

interface SmoothScrollContextType {
  getLenis: () => Lenis | null;
}

const SmoothScrollContext = createContext<SmoothScrollContextType>({ getLenis: () => null });

export function useSmoothScroll() {
  return useContext(SmoothScrollContext);
}

interface SmoothScrollProviderProps {
  children: ReactNode;
}

export function SmoothScrollProvider({ children }: SmoothScrollProviderProps) {
  const lenisRef = useRef<Lenis | null>(null);
  const getLenis = () => lenisRef.current;

  useEffect(() => {
    // Initialize Lenis
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
    });

    lenisRef.current = lenis;

    // Connect Lenis to GSAP ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update);

    // Use GSAP ticker for smooth animation
    gsap.ticker.add((time) => {
      lenis.raf(time * 1000);
    });

    gsap.ticker.lagSmoothing(0);

    // Cleanup
    return () => {
      lenis.destroy();
      lenisRef.current = null;
    };
  }, []);

  return (
    <SmoothScrollContext.Provider value={{ getLenis }}>
      {children}
    </SmoothScrollContext.Provider>
  );
}
