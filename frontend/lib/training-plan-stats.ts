import { parseISO } from 'date-fns';
import type { TrainingDay, TrainingPlanResponse } from '@/lib/types';

export interface MuscleGroupStat {
  muscle_group: string;
  count: number;
}

export interface DifficultyStat {
  difficulty: 'Novice' | 'Intermediate' | 'Advanced' | 'unknown';
  count: number;
}

export interface LongestDayStat {
  day: string;
  name: string;
  time_required: number;
}

export interface TrainingPlanStatsPayload {
  total_days: number;
  total_exercises: number;
  total_minutes: number;
  average_minutes_per_day: number;
  longest_day: LongestDayStat | null;
  difficulty_distribution: DifficultyStat[];
  muscle_distribution: MuscleGroupStat[];
}

function normalizeMuscleName(input: string): string {
  return input
    .trim()
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ');
}

function normalizeDifficulty(input?: string): DifficultyStat['difficulty'] {
  if (!input) return 'unknown';
  const normalized = input.toLowerCase().trim();
  if (normalized === 'novice') return 'Novice';
  if (normalized === 'intermediate') return 'Intermediate';
  if (normalized === 'advanced') return 'Advanced';
  return 'unknown';
}

function pickLongestDay(days: TrainingDay[]): LongestDayStat | null {
  if (days.length === 0) return null;

  const sorted = [...days].sort((a, b) => {
    if (b.timeRequired !== a.timeRequired) {
      return b.timeRequired - a.timeRequired;
    }
    return parseISO(a.day).getTime() - parseISO(b.day).getTime();
  });

  const top = sorted[0];
  return {
    day: top.day,
    name: top.name,
    time_required: top.timeRequired,
  };
}

export function buildTrainingPlanStats(plan: TrainingPlanResponse): TrainingPlanStatsPayload {
  const totalDays = plan.trainings.length;
  const totalExercises = plan.trainings.reduce((acc, day) => acc + day.exercises.length, 0);
  const totalMinutes = plan.trainings.reduce((acc, day) => acc + day.timeRequired, 0);
  const averageMinutesPerDay = totalDays > 0 ? Math.round(totalMinutes / totalDays) : 0;

  const difficultyCounter = new Map<DifficultyStat['difficulty'], number>([
    ['Novice', 0],
    ['Intermediate', 0],
    ['Advanced', 0],
    ['unknown', 0],
  ]);
  const muscleCounter = new Map<string, number>();

  plan.trainings.forEach((day) => {
    day.exercises.forEach((exercise) => {
      const difficultyKey = normalizeDifficulty(exercise.difficulty);
      difficultyCounter.set(difficultyKey, (difficultyCounter.get(difficultyKey) ?? 0) + 1);

      const primaryMuscles = exercise.primary_muscles?.filter(Boolean) ?? [];
      if (primaryMuscles.length > 0) {
        primaryMuscles.forEach((muscle) => {
          const key = normalizeMuscleName(muscle);
          if (!key) return;
          muscleCounter.set(key, (muscleCounter.get(key) ?? 0) + 1);
        });
      } else {
        (day.bodyParts ?? []).forEach((part) => {
          const key = normalizeMuscleName(part);
          if (!key) return;
          muscleCounter.set(key, (muscleCounter.get(key) ?? 0) + 1);
        });
      }
    });
  });

  const difficultyDistribution: DifficultyStat[] = [
    { difficulty: 'Novice', count: difficultyCounter.get('Novice') ?? 0 },
    { difficulty: 'Intermediate', count: difficultyCounter.get('Intermediate') ?? 0 },
    { difficulty: 'Advanced', count: difficultyCounter.get('Advanced') ?? 0 },
    { difficulty: 'unknown', count: difficultyCounter.get('unknown') ?? 0 },
  ];

  const muscleDistribution: MuscleGroupStat[] = Array.from(muscleCounter.entries())
    .map(([muscle_group, count]) => ({ muscle_group, count }))
    .sort((a, b) => b.count - a.count || a.muscle_group.localeCompare(b.muscle_group));

  return {
    total_days: totalDays,
    total_exercises: totalExercises,
    total_minutes: totalMinutes,
    average_minutes_per_day: averageMinutesPerDay,
    longest_day: pickLongestDay(plan.trainings),
    difficulty_distribution: difficultyDistribution,
    muscle_distribution: muscleDistribution,
  };
}
