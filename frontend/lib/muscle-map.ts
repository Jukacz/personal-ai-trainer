import type { TrainingDay } from '@/lib/types';

export type MuscleIntensityLevel = 0 | 1 | 2 | 3;
export type WeeklyMuscleIntensityLevel = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export type MuscleMapGroupId =
  | 'abdominals'
  | 'obliques'
  | 'hands'
  | 'forearms'
  | 'biceps'
  | 'front-shoulders'
  | 'chest'
  | 'traps'
  | 'quads'
  | 'calves'
  | 'hamstrings'
  | 'glutes'
  | 'triceps'
  | 'lats'
  | 'lowerback'
  | 'traps-middle'
  | 'rear-shoulders';

export type MuscleIntensityByGroup = Record<MuscleMapGroupId, MuscleIntensityLevel>;
export type WeeklyMuscleIntensityByGroup = Record<MuscleMapGroupId, WeeklyMuscleIntensityLevel>;
export type AnyMuscleIntensityByGroup = MuscleIntensityByGroup | WeeklyMuscleIntensityByGroup;

export const FRONT_GROUP_IDS: MuscleMapGroupId[] = [
  'abdominals',
  'obliques',
  'hands',
  'forearms',
  'biceps',
  'front-shoulders',
  'chest',
  'traps',
  'quads',
  'calves',
];

export const BACK_GROUP_IDS: MuscleMapGroupId[] = [
  'traps',
  'calves',
  'hamstrings',
  'glutes',
  'hands',
  'forearms',
  'triceps',
  'lats',
  'lowerback',
  'traps-middle',
  'rear-shoulders',
];

const ALL_GROUP_IDS: MuscleMapGroupId[] = [
  ...new Set<MuscleMapGroupId>([...FRONT_GROUP_IDS, ...BACK_GROUP_IDS]),
];

const MUSCLE_TO_GROUPS: Record<string, MuscleMapGroupId[]> = {
  abdominals: ['abdominals'],
  abs: ['abdominals'],
  core: ['abdominals', 'obliques', 'lowerback'],
  obliques: ['obliques'],

  chest: ['chest'],
  pectorals: ['chest'],
  pectoralis: ['chest'],

  biceps: ['biceps'],
  triceps: ['triceps'],
  forearms: ['forearms'],
  forearm: ['forearms'],
  hands: ['hands'],

  shoulders: ['front-shoulders', 'rear-shoulders'],
  shoulder: ['front-shoulders', 'rear-shoulders'],
  deltoids: ['front-shoulders', 'rear-shoulders'],
  deltoid: ['front-shoulders', 'rear-shoulders'],
  rearshoulders: ['rear-shoulders'],

  traps: ['traps', 'traps-middle'],
  trapezius: ['traps', 'traps-middle'],
  upperback: ['traps-middle', 'lats', 'rear-shoulders'],

  back: ['lats', 'traps-middle', 'lowerback'],
  lats: ['lats'],
  latissimus: ['lats'],
  latissimusdorsi: ['lats'],
  lowerback: ['lowerback'],
  erectorspinae: ['lowerback'],

  quads: ['quads'],
  quadriceps: ['quads'],
  hamstrings: ['hamstrings'],
  glutes: ['glutes'],
  gluteus: ['glutes'],
  calves: ['calves'],
};

function normalizeMuscleName(input: string): string {
  return input
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]/g, '');
}

function resolveMuscleGroups(muscle: string): MuscleMapGroupId[] {
  const normalized = normalizeMuscleName(muscle);
  const exact = MUSCLE_TO_GROUPS[normalized];
  if (exact) {
    return exact;
  }

  // Fallback heuristic for richer MuscleWiki labels, e.g. "upper chest".
  if (normalized.includes('chest') || normalized.includes('pectoral')) {
    return ['chest'];
  }
  if (normalized.includes('abdominal') || normalized.includes('abs')) {
    return ['abdominals'];
  }
  if (normalized.includes('oblique')) {
    return ['obliques'];
  }
  if (normalized.includes('core')) {
    return ['abdominals', 'obliques', 'lowerback'];
  }
  if (normalized.includes('bicep')) {
    return ['biceps'];
  }
  if (normalized.includes('tricep')) {
    return ['triceps'];
  }
  if (normalized.includes('forearm')) {
    return ['forearms'];
  }
  if (normalized.includes('delt') || normalized.includes('shoulder')) {
    return ['front-shoulders', 'rear-shoulders'];
  }
  if (normalized.includes('trap')) {
    return ['traps', 'traps-middle'];
  }
  if (normalized.includes('lat')) {
    return ['lats'];
  }
  if (normalized.includes('back')) {
    return ['lats', 'traps-middle', 'lowerback'];
  }
  if (normalized.includes('quad')) {
    return ['quads'];
  }
  if (normalized.includes('hamstring')) {
    return ['hamstrings'];
  }
  if (normalized.includes('glute')) {
    return ['glutes'];
  }
  if (normalized.includes('calf')) {
    return ['calves'];
  }

  return [];
}

function countToLevel(count: number): MuscleIntensityLevel {
  if (count <= 0) {
    return 0;
  }
  if (count === 1) {
    return 1;
  }
  if (count === 2) {
    return 2;
  }
  return 3;
}

export function buildMuscleIntensity(day: TrainingDay): MuscleIntensityByGroup {
  const counts = ALL_GROUP_IDS.reduce<Record<MuscleMapGroupId, number>>((acc, groupId) => {
    acc[groupId] = 0;
    return acc;
  }, {} as Record<MuscleMapGroupId, number>);

  let hasExerciseMuscleContext = false;

  for (const exercise of day.exercises) {
    const primaryMuscles = Array.isArray(exercise.primary_muscles)
      ? exercise.primary_muscles
      : [];

    const groupsForExercise = new Set<MuscleMapGroupId>();

    for (const muscle of primaryMuscles) {
      if (typeof muscle !== 'string' || !muscle.trim()) {
        continue;
      }
      const mappedGroups = resolveMuscleGroups(muscle);
      if (mappedGroups.length > 0) {
        hasExerciseMuscleContext = true;
      }
      for (const groupId of mappedGroups) {
        groupsForExercise.add(groupId);
      }
    }

    for (const groupId of groupsForExercise) {
      counts[groupId] += 1;
    }
  }

  if (!hasExerciseMuscleContext) {
    const bodyParts = Array.isArray(day.bodyParts) ? day.bodyParts : [];
    for (const part of bodyParts) {
      if (typeof part !== 'string' || !part.trim()) {
        continue;
      }
      for (const groupId of resolveMuscleGroups(part)) {
        counts[groupId] += 1;
      }
    }
  }

  return ALL_GROUP_IDS.reduce<MuscleIntensityByGroup>((acc, groupId) => {
    acc[groupId] = countToLevel(counts[groupId]);
    return acc;
  }, {} as MuscleIntensityByGroup);
}

function countToWeeklyLevel(count: number): WeeklyMuscleIntensityLevel {
  if (count <= 0) return 0;
  if (count === 1) return 1;
  if (count === 2) return 2;
  if (count === 3) return 3;
  if (count <= 5) return 4;
  if (count <= 7) return 5;
  return 6;
}

export function buildWeeklyMuscleIntensity(days: TrainingDay[]): WeeklyMuscleIntensityByGroup {
  const counts = ALL_GROUP_IDS.reduce<Record<MuscleMapGroupId, number>>((acc, groupId) => {
    acc[groupId] = 0;
    return acc;
  }, {} as Record<MuscleMapGroupId, number>);

  for (const day of days) {
    let dayHasExerciseMuscleContext = false;

    for (const exercise of day.exercises) {
      const primaryMuscles = Array.isArray(exercise.primary_muscles) ? exercise.primary_muscles : [];
      const groupsForExercise = new Set<MuscleMapGroupId>();

      for (const muscle of primaryMuscles) {
        if (typeof muscle !== 'string' || !muscle.trim()) {
          continue;
        }
        const mappedGroups = resolveMuscleGroups(muscle);
        if (mappedGroups.length > 0) {
          dayHasExerciseMuscleContext = true;
        }
        for (const groupId of mappedGroups) {
          groupsForExercise.add(groupId);
        }
      }

      for (const groupId of groupsForExercise) {
        counts[groupId] += 1;
      }
    }

    if (!dayHasExerciseMuscleContext) {
      const bodyParts = Array.isArray(day.bodyParts) ? day.bodyParts : [];
      for (const part of bodyParts) {
        if (typeof part !== 'string' || !part.trim()) {
          continue;
        }
        for (const groupId of resolveMuscleGroups(part)) {
          counts[groupId] += 1;
        }
      }
    }
  }

  return ALL_GROUP_IDS.reduce<WeeklyMuscleIntensityByGroup>((acc, groupId) => {
    acc[groupId] = countToWeeklyLevel(counts[groupId]);
    return acc;
  }, {} as WeeklyMuscleIntensityByGroup);
}
