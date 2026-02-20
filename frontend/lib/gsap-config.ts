import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger);

// Default ease for smooth animations
gsap.defaults({
  ease: 'power2.out',
  duration: 0.8,
});

// Export for use in components
export { gsap, ScrollTrigger };
