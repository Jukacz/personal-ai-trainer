import type { Metadata } from 'next';
import { BarChart3, CalendarDays, ListChecks, PlusCircle, Sparkles } from 'lucide-react';
import { UserMenu } from '@/components/auth/user-menu';
import { DashboardPanel } from '@/components/dashboard/dashboard-panel';

export const metadata: Metadata = {
  title: 'Dashboard - AI Personal Trainer',
  description: 'Generuj spersonalizowane plany treningowe za pomocą AI. Dostosowane do Twoich celów i możliwości.',
  keywords: ['trener personalny', 'plan treningowy', 'fitness', 'AI', 'ćwiczenia'],
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    title: 'Dashboard - AI Personal Trainer',
    description: 'Spersonalizowane plany treningowe generowane przez AI',
  },
};

export default function DashboardPage() {
  const navItems = [
    { href: '#overview', label: 'Przegląd', icon: Sparkles },
    { href: '#charts', label: 'Wykresy', icon: BarChart3 },
    { href: '#calendar', label: 'Kalendarz', icon: CalendarDays },
    { href: '#actions', label: 'Szybkie akcje', icon: PlusCircle },
    { href: '#recent-plans', label: 'Ostatnie plany', icon: ListChecks },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5">
      <div className="container mx-auto px-4 py-6 space-y-8">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Panel treningowy</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Monitoruj postęp i zarządzaj planami w jednym miejscu.
            </p>
          </div>
          <UserMenu />
        </div>

        <div className="grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">
          <aside className="dashboard-sidebar lg:sticky lg:top-6 lg:h-fit">
            <nav className="dashboard-nav-container rounded-xl border bg-card/70 p-3 backdrop-blur supports-[backdrop-filter]:bg-card/60">
              <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Nawigacja
              </p>
              <ul className="space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <li key={item.href} className="group/nav-item">
                      <a
                        href={item.href}
                        className="dashboard-nav-link flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors transition-transform hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 active:scale-[0.98]"
                      >
                        <Icon className="h-4 w-4 transition-transform group-hover/nav-item:translate-x-0.5" />
                        <span className="dashboard-nav-label">{item.label}</span>
                      </a>
                    </li>
                  );
                })}
              </ul>
            </nav>
          </aside>
          <DashboardPanel />
        </div>
      </div>
    </main>
  );
}
