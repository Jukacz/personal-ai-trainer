'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dumbbell, Home } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { pl } from 'date-fns/locale';
import type { Exercise, TrainingPlanResponse } from '@/lib/types';
import TrainingDayCard from './training-day-card';
import { buildTrainingPlanStats } from '@/lib/training-plan-stats';
import { TrainingPlanStats } from './training-plan-stats';

interface TrainingPlanClientProps {
  trainingPlan: TrainingPlanResponse | null;
  error?: string | null;
}

export function TrainingPlanClient({ trainingPlan, error }: TrainingPlanClientProps) {
  const router = useRouter();
  const [planState, setPlanState] = useState<TrainingPlanResponse | null>(trainingPlan);

  if (error || !planState) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5 flex items-center justify-center">
        <Card className="max-w-md mx-4 shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl">Błąd</CardTitle>
            <CardDescription>Nie udało się załadować planu treningowego</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">{error}</p>
            <Button onClick={() => router.push('/dashboard')} className="w-full">
              <Home className="mr-2 h-4 w-4" />
              Powrót do panelu
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const stats = buildTrainingPlanStats(planState);

  return (
    <main className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5">
      <div className="container mx-auto px-4 py-8 md:py-16">
        {/* Header */}
        <div className="text-center mb-12 space-y-4">
          <div className="flex items-center justify-center gap-3">
            <Dumbbell className="h-10 w-10 text-primary" />
            <h1 className="text-4xl md:text-5xl font-bold">Twój Plan Treningowy</h1>
          </div>
          <p className="text-lg text-muted-foreground">
            Wygenerowano: {format(parseISO(planState.created_at), 'PPP', { locale: pl })}
          </p>
          <Button onClick={() => router.push('/dashboard')} variant="outline" size="lg">
            <Home className="mr-2 h-5 w-5" />
            Powrót do panelu
          </Button>
        </div>

        <div className="mb-8">
          <TrainingPlanStats stats={stats} days={planState.trainings} />
        </div>

        {/* Training Days Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
          {planState.trainings.map((day, index) => (
            <TrainingDayCard
              key={index}
              trainingId={planState.id}
              day={day}
              dayNumber={index + 1}
              onExerciseReplaced={(payload: { day: string; exerciseIndex: number; exercise: Exercise; timeRequired: number; }) => {
                setPlanState((prev) => {
                  if (!prev) {
                    return prev;
                  }
                  const trainings = prev.trainings.map((item) => ({ ...item, exercises: [...item.exercises] }));
                  const dayIndex = trainings.findIndex((item) => item.day === payload.day);
                  if (dayIndex === -1) {
                    return prev;
                  }
                  trainings[dayIndex].exercises[payload.exerciseIndex] = payload.exercise;
                  trainings[dayIndex].timeRequired = payload.timeRequired;
                  return { ...prev, trainings };
                });
              }}
            />
          ))}
        </div>
      </div>
    </main>
  );
}
