'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { trainingApi } from '@/lib/api-client';
import { format } from 'date-fns';
import { pl } from 'date-fns/locale';
import { Dumbbell, Calendar, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TrainingListProps {
  limit?: number;
  className?: string;
  title?: string;
}

export function TrainingList({ limit = 20, className, title = 'Twoje plany treningowe' }: TrainingListProps) {
  const router = useRouter();

  // Fetch training list
  const { data: trainingListData, isLoading: isLoadingList, error: listError } = useQuery({
    queryKey: ['trainings-list', { limit, offset: 0 }],
    queryFn: () => trainingApi.getTrainingsList(limit, 0),
  });

  const getDifficultyLabel = (difficulty?: string): string => {
    switch (difficulty) {
      case 'Novice':
        return 'Początkujący';
      case 'Intermediate':
        return 'Średniozaawansowany';
      case 'Advanced':
        return 'Zaawansowany';
      default:
        return 'Nieznany';
    }
  };

  return (
    <div className={cn('max-w-2xl mx-auto mt-12', className)}>
      <h2 className="text-3xl font-bold mb-6 flex items-center gap-2">
        <TrendingUp className="h-8 w-8 text-primary" />
        {title}
      </h2>

      {/* Loading State */}
      {isLoadingList && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="shadow-md">
              <CardContent className="p-6">
                <div className="space-y-3">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-4 w-32" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {listError && (
        <Card className="shadow-md border-destructive/50">
          <CardContent className="p-6">
            <p className="text-sm text-destructive">
              Nie udało się załadować planów treningowych. Spróbuj odświeżyć stronę.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!isLoadingList && !listError && trainingListData?.trainings.length === 0 && (
        <Card className="shadow-md">
          <CardContent className="p-8 text-center">
            <Dumbbell className="h-16 w-16 text-muted-foreground mx-auto mb-4 opacity-50" />
            <p className="text-lg text-muted-foreground">
              Nie masz jeszcze żadnych planów treningowych
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Stwórz swój pierwszy plan korzystając z formularza powyżej
            </p>
          </CardContent>
        </Card>
      )}

      {/* Training List */}
      {!isLoadingList && !listError && trainingListData && trainingListData.trainings.length > 0 && (
        <div className="space-y-4">
          {trainingListData.trainings.map((training) => (
            <Card
              key={training.id}
              className="shadow-md hover:shadow-lg transition-all cursor-pointer hover:border-primary/50"
              onClick={() => router.push(`/training/${training.id}`)}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      <span>
                        Utworzono:{' '}
                        {format(new Date(training.created_at), 'dd MMMM yyyy, HH:mm', {
                          locale: pl,
                        })}
                      </span>
                    </div>
                    {training.difficulty && (
                      <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
                        <TrendingUp className="h-3.5 w-3.5" />
                        {getDifficultyLabel(training.difficulty)}
                      </div>
                    )}
                  </div>
                  <Button variant="ghost" size="sm">
                    Zobacz plan
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
