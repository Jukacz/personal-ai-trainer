'use client';

import { format, parseISO } from 'date-fns';
import { pl } from 'date-fns/locale';
import { BarChart3, Clock3, Dumbbell, Timer, Trophy } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { TrainingDay } from '@/lib/types';
import type { TrainingPlanStatsPayload } from '@/lib/training-plan-stats';
import WeeklyMuscleMapCard from './muscle-map/weekly-muscle-map-card';

interface TrainingPlanStatsProps {
  stats: TrainingPlanStatsPayload;
  days: TrainingDay[];
}

const MUSCLE_GROUP_PL_DICTIONARY: Record<string, string> = {
  abdominals: 'Mięśnie brzucha',
  abs: 'Mięśnie brzucha',
  obliques: 'Mięśnie skośne brzucha',
  chest: 'Klatka piersiowa',
  pectorals: 'Klatka piersiowa',
  pectoralis: 'Klatka piersiowa',
  biceps: 'Biceps',
  triceps: 'Triceps',
  forearms: 'Przedramiona',
  hands: 'Dłonie',
  shoulders: 'Barki',
  'front shoulders': 'Przedni akton barków',
  'rear shoulders': 'Tylny akton barków',
  deltoids: 'Naramienne',
  traps: 'Czworoboczne',
  'traps middle': 'Środkowe czworoboczne',
  back: 'Plecy',
  lats: 'Najszerzsze grzbietu',
  lowerback: 'Dolne plecy',
  lower_back: 'Dolne plecy',
  quads: 'Czworogłowe uda',
  quadriceps: 'Czworogłowe uda',
  hamstrings: 'Dwugłowe uda',
  glutes: 'Pośladki',
  calves: 'Łydki',
};

function toPolishDifficultyLabel(value: 'Novice' | 'Intermediate' | 'Advanced' | 'unknown'): string {
  switch (value) {
    case 'Novice':
      return 'Początkujący';
    case 'Intermediate':
      return 'Średniozaawansowany';
    case 'Advanced':
      return 'Zaawansowany';
    default:
      return 'Nieokreślony';
  }
}

function toTitleCase(value: string): string {
  return value
    .split(' ')
    .filter(Boolean)
    .map((chunk) => chunk[0]?.toUpperCase() + chunk.slice(1))
    .join(' ');
}

function toPolishMuscleLabel(value: string): string {
  const normalized = value.trim().toLowerCase();
  return MUSCLE_GROUP_PL_DICTIONARY[normalized] ?? toTitleCase(value);
}

export function TrainingPlanStats({ stats, days }: TrainingPlanStatsProps) {
  const topMuscles = stats.muscle_distribution.slice(0, 8);

  return (
    <Card className="shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          Statystyki planu
        </CardTitle>
        <CardDescription>Podsumowanie wygenerowanego planu treningowego.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Liczba dni treningowych</p>
            <p className="text-2xl font-semibold flex items-center gap-2">
              <Timer className="h-4 w-4 text-primary" />
              {stats.total_days}
            </p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Liczba ćwiczeń</p>
            <p className="text-2xl font-semibold flex items-center gap-2">
              <Dumbbell className="h-4 w-4 text-primary" />
              {stats.total_exercises}
            </p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Łączny czas planu</p>
            <p className="text-2xl font-semibold flex items-center gap-2">
              <Clock3 className="h-4 w-4 text-primary" />
              {stats.total_minutes} min
            </p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Średni czas na dzień</p>
            <p className="text-2xl font-semibold">{stats.average_minutes_per_day} min</p>
          </div>
        </div>

        <div className="rounded-lg border p-3">
          <p className="text-sm font-medium flex items-center gap-2">
            <Trophy className="h-4 w-4 text-primary" />
            Najdłuższy dzień
          </p>
          {stats.longest_day ? (
            <p className="text-sm text-muted-foreground mt-1">
              {stats.longest_day.name} • {format(parseISO(stats.longest_day.day), 'PPP', { locale: pl })} •{' '}
              {stats.longest_day.time_required} min
            </p>
          ) : (
            <p className="text-sm text-muted-foreground mt-1">Brak danych</p>
          )}
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">Rozkład poziomów trudności</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {stats.difficulty_distribution.map((item) => (
              <div key={item.difficulty} className="rounded-md border px-3 py-2 text-sm flex items-center justify-between">
                <span>{toPolishDifficultyLabel(item.difficulty)}</span>
                <span className="font-semibold">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">Partie mięśniowe (TOP)</p>
          <div className="grid gap-4 lg:grid-cols-2">
            <WeeklyMuscleMapCard days={days} />
            {topMuscles.length > 0 ? (
              <div className="space-y-1.5">
                {topMuscles.map((muscle) => (
                  <div
                    key={muscle.muscle_group}
                    className="rounded-md border px-3 py-2 text-sm flex items-center justify-between"
                  >
                    <span>{toPolishMuscleLabel(muscle.muscle_group)}</span>
                    <span className="font-semibold">{muscle.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Brak danych o partiach mięśniowych.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
