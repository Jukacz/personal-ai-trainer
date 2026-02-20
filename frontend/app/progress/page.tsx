'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { pollTaskStatus } from '@/lib/api-client';
import type { TaskStatusResponse } from '@/lib/types';
import { Dumbbell, CheckCircle2, XCircle, Loader2, Home } from 'lucide-react';

function ProgressContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskId = searchParams.get('task_id');

  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) {
      return;
    }

    const startPolling = async () => {
      try {
        const result = await pollTaskStatus(
          taskId,
          (status) => {
            setTaskStatus(status);
          },
          3000, // Poll every 3 seconds
          100 // Max 100 attempts (5 minutes)
        );

        // Final status
        setTaskStatus(result);

        // If completed successfully, redirect to training plan
        if (result.status === 'completed' && result.result?.training_id) {
          setTimeout(() => {
            router.push(`/training/${result.result!.training_id}`);
          }, 1500);
        }
      } catch (err) {
        console.error('Polling error:', err);
        setError(
          err instanceof Error ? err.message : 'Wystąpił błąd podczas generowania planu'
        );
      }
    };

    startPolling();
  }, [taskId, router]);

  if (error || !taskId) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5 flex items-center justify-center">
        <Card className="max-w-md mx-4 shadow-xl">
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <XCircle className="h-8 w-8 text-destructive" />
              <CardTitle className="text-2xl">Błąd</CardTitle>
            </div>
            <CardDescription>Nie udało się przetworzyć żądania</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">{error || 'Brak identyfikatora zadania'}</p>
            <Button onClick={() => router.push('/')} className="w-full">
              <Home className="mr-2 h-4 w-4" />
              Powrót do strony głównej
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const isCompleted = taskStatus?.status === 'completed';
  const isFailed = taskStatus?.status === 'failed';
  const isProcessing = taskStatus?.status === 'processing' || taskStatus?.status === 'pending';

  return (
    <main className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5 flex items-center justify-center">
      <Card className="max-w-2xl mx-4 shadow-xl">
        <CardHeader>
          <div className="flex items-center gap-3 mb-2">
            {isCompleted && <CheckCircle2 className="h-8 w-8 text-green-500" />}
            {isFailed && <XCircle className="h-8 w-8 text-destructive" />}
            {isProcessing && (
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
            )}
            <CardTitle className="text-2xl">
              {isCompleted && 'Plan gotowy!'}
              {isFailed && 'Błąd generowania'}
              {isProcessing && 'Generowanie planu...'}
            </CardTitle>
          </div>
          <CardDescription>
            {isCompleted && 'Twój plan treningowy został wygenerowany pomyślnie'}
            {isFailed && 'Wystąpił problem podczas tworzenia planu'}
            {isProcessing && 'Proszę czekać, to może potrwać 1-3 minuty'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Status Message */}
          <div className="p-4 bg-accent/30 rounded-lg">
            <p className="text-sm font-medium">
              {taskStatus?.message || 'Inicjalizacja...'}
            </p>
          </div>

          {/* Progress Indicator */}
          {isProcessing && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Dumbbell className="h-4 w-4 animate-pulse" />
                <span>AI analizuje Twoje parametry i tworzy optymalny plan...</span>
              </div>
            </div>
          )}

          {/* Success Message */}
          {isCompleted && (
            <div className="space-y-4">
              <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                <p className="text-sm text-green-700 dark:text-green-400">
                  Plan treningowy został wygenerowany! Za chwilę zostaniesz przekierowany...
                </p>
              </div>
              <Button
                onClick={() =>
                  router.push(`/training/${taskStatus.result!.training_id}`)
                }
                className="w-full"
                size="lg"
              >
                <CheckCircle2 className="mr-2 h-5 w-5" />
                Zobacz plan treningowy
              </Button>
            </div>
          )}

          {/* Error Message */}
          {isFailed && (
            <div className="space-y-4">
              <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg">
                <p className="text-sm text-destructive">
                  {taskStatus?.error || 'Nieznany błąd'}
                </p>
              </div>
              <Button onClick={() => router.push('/')} variant="outline" className="w-full">
                <Home className="mr-2 h-4 w-4" />
                Spróbuj ponownie
              </Button>
            </div>
          )}

          {/* Estimated Time */}
          {isProcessing && (
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-75" />
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-150" />
              </div>
              <span>Szacowany czas: 1-3 minuty</span>
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

export default function ProgressPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5 flex items-center justify-center">
          <Card className="max-w-2xl mx-4 shadow-xl">
            <CardContent className="p-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto" />
            </CardContent>
          </Card>
        </main>
      }
    >
      <ProgressContent />
    </Suspense>
  );
}
