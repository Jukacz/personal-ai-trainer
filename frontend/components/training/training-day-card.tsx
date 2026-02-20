'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Accordion } from '@/components/ui/accordion';
import { Calendar, Clock } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { pl } from 'date-fns/locale';
import type { Exercise, TrainingDay } from '@/lib/types';
import { trainingApi } from '@/lib/api-client';
import ExerciseItem from './exercise-item';
import MuscleMapCard from './muscle-map/muscle-map-card';

interface TrainingDayCardProps {
  trainingId?: string;
  day: TrainingDay;
  dayNumber?: number;
  showDayNumber?: boolean;
  onExerciseReplaced?: (payload: {
    day: string;
    exerciseIndex: number;
    exercise: Exercise;
    timeRequired: number;
  }) => void;
}

export default function TrainingDayCard({
  trainingId,
  day,
  dayNumber,
  showDayNumber = true,
  onExerciseReplaced,
}: TrainingDayCardProps) {
  const dayDate = parseISO(day.day);
  const dayName = format(dayDate, 'EEEE', { locale: pl });
  const dateFormatted = format(dayDate, 'dd MMMM', { locale: pl });
  const { data: progressData } = useQuery({
    queryKey: ['training-progress', trainingId, day.day],
    queryFn: () => trainingApi.getTrainingProgress(trainingId!, day.day),
    enabled: Boolean(trainingId),
  });
  const completedSet = useMemo(
    () => new Set(progressData?.completed_exercise_indices ?? []),
    [progressData?.completed_exercise_indices]
  );
  const notCompletedSet = useMemo(
    () => new Set(progressData?.not_completed_exercise_indices ?? []),
    [progressData?.not_completed_exercise_indices]
  );

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium text-muted-foreground capitalize">
              {dayName}
            </span>
          </div>
          {showDayNumber && typeof dayNumber === 'number' && (
            <span className="text-xs bg-primary/10 text-primary px-3 py-1 rounded-full font-medium">
              Dzień {dayNumber}
            </span>
          )}
        </div>
        <CardTitle className="text-xl">{day.name}</CardTitle>
        <CardDescription className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          <span>{day.timeRequired} minut</span>
        </CardDescription>
        <p className="text-sm text-muted-foreground">{dateFormatted}</p>
      </CardHeader>
      <CardContent>
        <MuscleMapCard day={day} />
        <Accordion type="multiple" className="w-full">
          {day.exercises.map((exercise, index) => (
            <ExerciseItem
              key={index}
              trainingId={trainingId}
              trainingDay={day.day}
              exercise={exercise}
              exerciseIndex={index}
              exerciseNumber={index + 1}
              isCompleted={completedSet.has(index)}
              isNotCompleted={notCompletedSet.has(index)}
              notCompletedReason={progressData?.not_completed_reasons_by_exercise_index[String(index)]}
              prefilledOpinion={
                typeof exercise.exercise_id === 'number'
                  ? progressData?.opinions_by_exercise_id[String(exercise.exercise_id)]
                  : undefined
              }
              onExerciseReplaced={onExerciseReplaced}
            />
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
