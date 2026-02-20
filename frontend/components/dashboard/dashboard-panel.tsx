'use client';

import { useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, XAxis, YAxis } from 'recharts';
import { Activity, CalendarRange, CircleOff, Flame } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import { getDashboardAnalytics, type StatusDistributionPoint } from '@/lib/dashboard-analytics';
import { TrainingCalendarPanel } from '@/components/home/training-calendar-panel';
import { TrainingForm } from '@/components/home/training-form';
import { TrainingList } from '@/components/home/training-list';
import { MetricList } from '@/components/dashboard/metric-list';
import { cn } from '@/lib/utils';

type ChartSectionId = 'trend' | 'status' | 'weekday';
type ChartCardMeta = {
  id: ChartSectionId;
  title: string;
  description: string;
} & Readonly<{
  borderClass: string;
}>;

const CHART_CARD_META: Readonly<Record<ChartSectionId, ChartCardMeta>> = {
  trend: {
    id: 'trend',
    title: 'Trend zaplanowanych dni',
    description: 'Ostatnie 30 dni',
    borderClass: 'border-l-[var(--chart-1)]',
  },
  status: {
    id: 'status',
    title: 'Status ćwiczeń',
    description: 'Wykonane vs niewykonane vs oczekujące',
    borderClass: 'border-l-[var(--chart-2)]',
  },
  weekday: {
    id: 'weekday',
    title: 'Rozkład dni tygodnia',
    description: 'Ile treningów przypada na każdy dzień tygodnia',
    borderClass: 'border-l-[var(--chart-5)]',
  },
};

const chartConfig = {
  trainings: { label: 'Treningi', color: 'var(--chart-1)' },
  completed: { label: 'Wykonane', color: 'var(--chart-2)' },
  not_completed: { label: 'Niewykonane', color: 'var(--chart-3)' },
  pending: { label: 'Oczekujące', color: 'var(--chart-4)' },
  weekdays: { label: 'Dni', color: 'var(--chart-5)' },
} satisfies ChartConfig;

function isStatusDistributionPoint(item: unknown): item is StatusDistributionPoint {
  if (typeof item !== 'object' || item === null) {
    return false;
  }

  const status = (item as { status?: unknown }).status;
  const value = (item as { value?: unknown }).value;
  return (
    (status === 'completed' || status === 'not_completed' || status === 'pending') &&
    typeof value === 'number'
  );
}

function getChartCardClass(section: ChartSectionId): string;
function getChartCardClass(section: ChartSectionId, activeSection: ChartSectionId | null): string;
function getChartCardClass(section: ChartSectionId, activeSection: ChartSectionId | null = null): string {
  const isActive = activeSection === section;
  return cn(
    'shadow-sm border-l-4 transition-colors',
    CHART_CARD_META[section].borderClass,
    isActive ? 'ring-1 ring-primary/30' : 'ring-0'
  );
}

function KpiSkeleton() {
  return (
    <Card className="shadow-sm">
      <CardHeader className="space-y-2">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-8 w-20" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full" />
      </CardContent>
    </Card>
  );
}

function ChartSkeleton() {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <Skeleton className="h-5 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-[260px] w-full" />
      </CardContent>
    </Card>
  );
}

export function DashboardPanel() {
  const [activeChartSection, setActiveChartSection] = useState<ChartSectionId | null>(null);
  const chartCardRefs = useRef<Record<ChartSectionId, HTMLDivElement | null>>({
    trend: null,
    status: null,
    weekday: null,
  });

  const {
    data: analytics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['dashboard-analytics', { windowDays: 30 }],
    queryFn: () => getDashboardAnalytics(30),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const safeStatusDistribution = useMemo(
    () => (analytics?.status_distribution ?? []).filter(isStatusDistributionPoint),
    [analytics?.status_distribution]
  );
  const statusData = useMemo(
    () =>
      safeStatusDistribution.map((item) => ({
        ...item,
        id: item.status,
        label:
          item.status === 'completed'
            ? 'Wykonane'
            : item.status === 'not_completed'
              ? 'Niewykonane'
              : 'Oczekujące',
        fill:
          item.status === 'completed'
            ? 'var(--color-completed)'
            : item.status === 'not_completed'
              ? 'var(--color-not_completed)'
              : 'var(--color-pending)',
      })),
    [safeStatusDistribution]
  );
  const trendData = useMemo(() => analytics?.training_trend ?? [], [analytics]);
  const weekdayData = useMemo(() => analytics?.weekday_distribution ?? [], [analytics]);
  const hasNoData = !isLoading && !error && (analytics?.kpis.scheduled_trainings ?? 0) === 0;

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      <section id="overview" className="scroll-mt-20 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          <>
            <KpiSkeleton />
            <KpiSkeleton />
            <KpiSkeleton />
            <KpiSkeleton />
          </>
        ) : (
          <>
            <Card className="shadow-sm">
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <CalendarRange className="h-4 w-4 text-primary" />
                  Zaplanowane treningi (30 dni)
                </CardDescription>
                <CardTitle className="text-3xl">{analytics?.kpis.scheduled_trainings ?? 0}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="shadow-sm">
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  Wykonane ćwiczenia
                </CardDescription>
                <CardTitle className="text-3xl">{analytics?.kpis.completed_exercises_percent ?? 0}%</CardTitle>
              </CardHeader>
            </Card>
            <Card className="shadow-sm">
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <CircleOff className="h-4 w-4 text-primary" />
                  Niewykonane ćwiczenia
                </CardDescription>
                <CardTitle className="text-3xl">{analytics?.kpis.not_completed_exercises ?? 0}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="shadow-sm">
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Flame className="h-4 w-4 text-primary" />
                  Najaktywniejszy dzień
                </CardDescription>
                <CardTitle className="text-3xl">{analytics?.kpis.most_active_weekday ?? 'Brak danych'}</CardTitle>
              </CardHeader>
            </Card>
          </>
        )}
      </section>

      {error && (
        <Card className="border-destructive/40">
          <CardContent className="py-6">
            <p className="text-sm text-destructive">
              Nie udało się załadować analityki dashboardu. Spróbuj odświeżyć stronę.
            </p>
          </CardContent>
        </Card>
      )}

      {hasNoData && (
        <Card>
          <CardContent className="py-6">
            <p className="text-sm text-muted-foreground">
              Brak danych z ostatnich 30 dni. Wygeneruj plan lub wykonaj trening, aby zobaczyć wykresy.
            </p>
          </CardContent>
        </Card>
      )}

      <section id="charts" className="scroll-mt-20 grid gap-6 xl:grid-cols-3">
        {isLoading ? (
          <>
            <ChartSkeleton />
            <ChartSkeleton />
            <ChartSkeleton />
          </>
        ) : (
          <>
            <div
              ref={(node) => {
                chartCardRefs.current.trend = node;
              }}
              className="xl:col-span-2"
              onMouseEnter={() => setActiveChartSection('trend')}
              onMouseLeave={() => setActiveChartSection(null)}
            >
              <Card className={getChartCardClass('trend', activeChartSection)}>
                <CardHeader>
                  <CardTitle>{CHART_CARD_META.trend.title}</CardTitle>
                  <CardDescription>{CHART_CARD_META.trend.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ChartContainer config={chartConfig} className="h-[260px] w-full">
                    <LineChart data={trendData}>
                      <CartesianGrid vertical={false} />
                      <XAxis
                        dataKey="date"
                        tickLine={false}
                        axisLine={false}
                        minTickGap={24}
                        tickFormatter={(value: string) => value.slice(5)}
                      />
                      <YAxis allowDecimals={false} width={24} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Line
                        type="monotone"
                        dataKey="count"
                        stroke="var(--color-trainings)"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ChartContainer>
                </CardContent>
              </Card>
            </div>

            <div
              ref={(node) => {
                chartCardRefs.current.status = node;
              }}
              onMouseEnter={() => setActiveChartSection('status')}
              onMouseLeave={() => setActiveChartSection(null)}
            >
              <Card className={getChartCardClass('status', activeChartSection)}>
                <CardHeader>
                  <CardTitle>{CHART_CARD_META.status.title}</CardTitle>
                  <CardDescription>{CHART_CARD_META.status.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ChartContainer config={chartConfig} className="h-[260px] w-full">
                    <PieChart>
                      <ChartTooltip content={<ChartTooltipContent nameKey="label" />} />
                      <Pie data={statusData} dataKey="value" nameKey="label" innerRadius={55} outerRadius={85}>
                        {statusData.map((entry) => (
                          <Cell key={entry.status} fill={entry.fill} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ChartContainer>
                  <MetricList items={statusData} className="mt-4" />
                </CardContent>
              </Card>
            </div>

            <div
              ref={(node) => {
                chartCardRefs.current.weekday = node;
              }}
              className="xl:col-span-3"
              onMouseEnter={() => setActiveChartSection('weekday')}
              onMouseLeave={() => setActiveChartSection(null)}
            >
              <Card className={getChartCardClass('weekday', activeChartSection)}>
                <CardHeader>
                  <CardTitle>{CHART_CARD_META.weekday.title}</CardTitle>
                  <CardDescription>{CHART_CARD_META.weekday.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ChartContainer config={chartConfig} className="h-[260px] w-full">
                    <BarChart data={weekdayData}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="weekday" tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} width={24} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="count" fill="var(--color-weekdays)" radius={6} />
                    </BarChart>
                  </ChartContainer>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] items-start">
        <div id="calendar" className="scroll-mt-20">
          <TrainingCalendarPanel />
        </div>
        <div id="actions" className="scroll-mt-20 space-y-4">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Szybkie akcje</CardTitle>
              <CardDescription>Wygeneruj plan tygodniowy lub szybki trening na dziś.</CardDescription>
            </CardHeader>
          </Card>
          <TrainingForm className="max-w-none mx-0" />
        </div>
      </section>

      <section id="recent-plans" className="scroll-mt-20">
        <TrainingList limit={8} className="mt-0 max-w-none" title="Ostatnie plany treningowe" />
      </section>
    </div>
  );
}
