'use client';

import { useMemo, useState } from 'react';
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';
import { format, parseISO } from 'date-fns';
import { pl } from 'date-fns/locale';
import { CalendarDays, Dumbbell } from 'lucide-react';
import { trainingApi } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Calendar } from '@/components/ui/calendar';
import TrainingDayCard from '@/components/training/training-day-card';

export function TrainingCalendarPanel() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const {
    data: calendarDaysData,
    isLoading: isCalendarLoading,
    error: calendarError,
  } = useQuery({
    queryKey: ['training-calendar-days'],
    queryFn: () => trainingApi.getTrainingCalendarDays(),
  });

  const dayToTrainingIdMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const day of calendarDaysData?.days ?? []) {
      if (!map.has(day.date)) {
        map.set(day.date, day.training_id);
      }
    }
    return map;
  }, [calendarDaysData]);

  const markedDates = useMemo(
    () => (calendarDaysData?.days ?? []).map((day) => parseISO(day.date)),
    [calendarDaysData]
  );

  const selectedIso = format(selectedDate, 'yyyy-MM-dd');
  const selectedTrainingId = dayToTrainingIdMap.get(selectedIso) ?? null;

  const {
    data: selectedPlan,
    isLoading: isSelectedPlanLoading,
    error: selectedPlanError,
  } = useQuery({
    queryKey: ['training-plan', selectedTrainingId],
    queryFn: () => trainingApi.getTrainingPlan(selectedTrainingId!),
    enabled: Boolean(selectedTrainingId),
  });

  const selectedTrainingDay = useMemo(
    () => selectedPlan?.trainings.find((day) => day.day === selectedIso) ?? null,
    [selectedPlan, selectedIso]
  );

  const hasDuplicateDateError =
    axios.isAxiosError(calendarError) && calendarError.response?.status === 409;

  return (
    <div className="space-y-6">
      <Card className="shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <CalendarDays className="h-6 w-6 text-primary" />
            Kalendarz treningów
          </CardTitle>
          <CardDescription>Zaznaczone są dni, w których masz już zapisany trening</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          {isCalendarLoading ? (
            <Skeleton className="h-[320px] w-full max-w-[320px]" />
          ) : hasDuplicateDateError ? (
            <p className="text-sm text-destructive text-center">
              Wykryto niespójność danych (duplikaty treningów w tej samej dacie). Skontaktuj się z administratorem.
            </p>
          ) : calendarError ? (
            <p className="text-sm text-destructive">Nie udało się załadować danych kalendarza.</p>
          ) : (
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => setSelectedDate(date ?? new Date())}
              locale={pl}
              modifiers={{ hasTraining: markedDates }}
              modifiersClassNames={{
                hasTraining:
                  'bg-primary/20 text-primary font-semibold rounded-md border border-primary/40',
              }}
              className="rounded-md border"
            />
          )}
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Dumbbell className="h-6 w-6 text-primary" />
          Trening na {format(selectedDate, 'd MMMM yyyy', { locale: pl })}
        </h2>

        {isSelectedPlanLoading && <Skeleton className="h-[240px] w-full" />}

        {!isSelectedPlanLoading && selectedPlanError && (
          <Card className="shadow-md border-destructive/50">
            <CardContent className="p-6">
              <p className="text-sm text-destructive">Nie udało się pobrać szczegółów treningu.</p>
            </CardContent>
          </Card>
        )}

        {!isSelectedPlanLoading && !selectedPlanError && selectedTrainingDay && (
          <TrainingDayCard
            trainingId={selectedPlan?.id}
            day={selectedTrainingDay}
            showDayNumber={false}
          />
        )}

        {!isSelectedPlanLoading && !selectedPlanError && !selectedTrainingDay && (
          <Card className="shadow-md">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Brak treningu w wybranym dniu.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
