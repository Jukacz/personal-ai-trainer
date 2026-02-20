'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { addDays } from 'date-fns';
import { z } from 'zod';
import { useForm, useWatch, Controller, type FieldPath } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { trainingApi } from '@/lib/api-client';
import { Dumbbell, Loader2 } from 'lucide-react';
import { useAuth } from '@/components/providers/auth-provider';
import type { DayOfWeek } from '@/lib/types';
import { cn } from '@/lib/utils';

type TrainingMode = 'plan' | 'quick';
type PlanStep = 0 | 1;

const DAY_OPTIONS: Array<{ value: DayOfWeek; label: string }> = [
  { value: 'monday', label: 'Poniedziałek' },
  { value: 'tuesday', label: 'Wtorek' },
  { value: 'wednesday', label: 'Środa' },
  { value: 'thursday', label: 'Czwartek' },
  { value: 'friday', label: 'Piątek' },
  { value: 'saturday', label: 'Sobota' },
  { value: 'sunday', label: 'Niedziela' },
];

const dayOfWeekSchema = z.enum([
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
]);

const planFormSchema = z
  .object({
    difficulty: z.enum(['Novice', 'Intermediate', 'Advanced']),
    age: z.number().min(16, 'Wiek musi być w zakresie 16-100 lat').max(100, 'Wiek musi być w zakresie 16-100 lat'),
    weight: z.number().min(30, 'Waga musi być w zakresie 30-300 kg').max(300, 'Waga musi być w zakresie 30-300 kg'),
    target_weight: z
      .number()
      .min(30, 'Waga docelowa musi być w zakresie 30-300 kg')
      .max(300, 'Waga docelowa musi być w zakresie 30-300 kg'),
    start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Podaj poprawną datę początkową (YYYY-MM-DD).'),
    end_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Podaj poprawną datę końcową (YYYY-MM-DD).'),
    trainings_per_week: z
      .number()
      .int('Liczba treningów tygodniowo musi być pełną liczbą')
      .min(1, 'Liczba treningów tygodniowo musi być w zakresie 1-6')
      .max(6, 'Liczba treningów tygodniowo musi być w zakresie 1-6'),
    selected_days: z.array(dayOfWeekSchema).min(1).max(6),
  })
  .refine((data) => data.start_date <= data.end_date, {
    path: ['end_date'],
    message: 'Data początkowa nie może być późniejsza od końcowej',
  })
  .refine((data) => data.selected_days.length === data.trainings_per_week, {
    path: ['selected_days'],
    message: 'Liczba wybranych dni musi być równa liczbie treningów tygodniowo',
  })
  .refine((data) => data.target_weight <= data.weight, {
    path: ['target_weight'],
    message: 'Waga docelowa powinna być mniejsza lub równa aktualnej',
  });

type PlanFormValues = z.infer<typeof planFormSchema>;

const planStepFields: Readonly<Record<PlanStep, FieldPath<PlanFormValues>[]>> = {
  0: ['difficulty', 'age', 'weight', 'target_weight'],
  1: ['start_date', 'end_date', 'trainings_per_week', 'selected_days'],
};
const PLAN_STEP_LABELS: Readonly<Record<PlanStep, string>> = {
  0: 'Cel',
  1: 'Intensywność',
};

function getTodayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

interface TrainingFormProps {
  className?: string;
}

export function TrainingForm({ className }: TrainingFormProps) {
  const router = useRouter();
  const { user } = useAuth();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConflictDialogOpen, setIsConflictDialogOpen] = useState(false);
  const [pendingConflictDates, setPendingConflictDates] = useState<string[]>([]);
  const [mode, setMode] = useState<TrainingMode>('plan');
  const [planStep, setPlanStep] = useState<PlanStep>(0);

  const form = useForm<PlanFormValues>({
    resolver: zodResolver(planFormSchema),
    defaultValues: {
      age: 25,
      weight: 75,
      target_weight: 70,
      difficulty: 'Intermediate',
      start_date: getTodayISO(),
      end_date: addDays(new Date(), 13).toISOString().slice(0, 10),
      trainings_per_week: 3,
      selected_days: ['monday', 'wednesday', 'friday'],
    },
    mode: 'onChange',
  });

  const {
    control,
    register,
    handleSubmit,
    setValue,
    trigger,
    getValues,
    formState: { errors },
  } = form;

  const values = useWatch({ control });

  useEffect(() => {
    if (user?.profile) {
      const timerId = window.setTimeout(() => {
        setValue('age', user.profile.age ?? 25);
        setValue('weight', user.profile.weight ?? 75);
        setValue('target_weight', user.profile.target_weight ?? 70);
      }, 0);

      return () => window.clearTimeout(timerId);
    }
  }, [setValue, user]);

  const canGoNext = useMemo(() => {
    const safeValues = values ?? {};
    if (planStep === 0) {
      return (
        (safeValues.age ?? 0) >= 16 &&
        (safeValues.weight ?? 0) >= 30 &&
        (safeValues.target_weight ?? 0) >= 30 &&
        Boolean(safeValues.difficulty)
      );
    }

    return (
      Boolean(safeValues.start_date) &&
      Boolean(safeValues.end_date) &&
      (safeValues.trainings_per_week ?? 0) >= 1 &&
      (safeValues.selected_days?.length ?? 0) > 0
    );
  }, [planStep, values]);

  const handlePlanSubmit = async (planData: PlanFormValues) => {
    const conflictPayload = {
      start_date: planData.start_date,
      end_date: planData.end_date,
      trainings_per_week: planData.trainings_per_week,
      selected_days: planData.selected_days,
    };

    const conflicts = await trainingApi.getTrainingConflicts(conflictPayload);
    if (conflicts.has_conflicts) {
      setPendingConflictDates(conflicts.conflict_dates);
      setIsConflictDialogOpen(true);
      setIsLoading(false);
      return;
    }

    const response = await trainingApi.createTraining({
      ...planData,
      conflict_dates: [],
      overwrite_conflicts: false,
    });

    router.push(`/progress?task_id=${response.task_id}`);
  };

  const handleQuickSubmit = async () => {
    const conflicts = await trainingApi.getQuickTrainingConflicts({});
    if (conflicts.has_conflicts) {
      setPendingConflictDates(conflicts.conflict_dates);
      setIsConflictDialogOpen(true);
      setIsLoading(false);
      return;
    }

    const response = await trainingApi.createQuickTraining({
      difficulty: getValues('difficulty'),
    });

    router.push(`/progress?task_id=${response.task_id}`);
  };

  const onSubmitPlan = async (planData: PlanFormValues) => {
    setError(null);
    setIsLoading(true);

    try {
      await handlePlanSubmit(planData);
    } catch (err) {
      console.error('Error creating training:', err);
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        const conflictDates = (err.response.data?.details?.conflict_dates as string[] | undefined) ?? [];
        setPendingConflictDates(conflictDates);
        setIsConflictDialogOpen(true);
        setIsLoading(false);
        return;
      }

      setError('Wystąpił błąd podczas tworzenia treningu. Spróbuj ponownie.');
      setIsLoading(false);
    }
  };

  const submitQuickMode = async () => {
    setError(null);
    setIsLoading(true);

    try {
      await handleQuickSubmit();
    } catch (err) {
      console.error('Error creating quick training:', err);
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        const conflictDates = (err.response.data?.details?.conflict_dates as string[] | undefined) ?? [];
        setPendingConflictDates(conflictDates);
        setIsConflictDialogOpen(true);
        setIsLoading(false);
        return;
      }

      setError('Wystąpił błąd podczas tworzenia treningu. Spróbuj ponownie.');
      setIsLoading(false);
    }
  };

  const submitPlanFromFinalStep = async () => {
    const isCurrentStepValid = await trigger(planStepFields[planStep], { shouldFocus: true });
    if (!isCurrentStepValid) return;
    await handleSubmit(onSubmitPlan)();
  };

  const handleOverwriteConfirm = async () => {
    setError(null);
    setIsLoading(true);

    try {
      const valuesSnapshot = getValues();
      const response =
        mode === 'plan'
          ? await trainingApi.createTraining({
              ...valuesSnapshot,
              overwrite_conflicts: true,
              conflict_dates: pendingConflictDates,
            })
          : await trainingApi.createQuickTraining(
              {
                difficulty: valuesSnapshot.difficulty,
              },
              true
            );

      setIsConflictDialogOpen(false);
      router.push(`/progress?task_id=${response.task_id}`);
    } catch (err) {
      console.error('Error creating training with overwrite:', err);
      const errorMessage =
        axios.isAxiosError(err) && err.response?.status === 409
          ? 'Wykryto nowe konflikty dat. Odśwież i spróbuj ponownie.'
          : 'Wystąpił błąd podczas tworzenia treningu. Spróbuj ponownie.';
      setError(errorMessage);
      setIsConflictDialogOpen(false);
      setIsLoading(false);
    }
  };

  const goToNextPlanStep = async () => {
    const isCurrentStepValid = await trigger(planStepFields[planStep], { shouldFocus: true });
    if (!isCurrentStepValid) return;
    setPlanStep((prev) => (prev < 1 ? 1 : prev));
  };

  const goToPreviousPlanStep = () => setPlanStep((prev) => (prev > 0 ? 0 : prev));

  return (
    <Card className={cn('max-w-2xl mx-auto shadow-xl', className)}>
      <CardHeader>
        <CardTitle className="text-2xl">Utwórz trening</CardTitle>
        <CardDescription>
          Wybierz szybki trening na dziś albo pełny plan treningowy w wybranym zakresie dat.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            onSubmit={(event) => {
              event.preventDefault();
            }}
            className="space-y-6"
          >
          <div className="space-y-2">
            <Label className="text-base">Tryb tworzenia</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={mode === 'plan' ? 'default' : 'outline'}
                onClick={() => {
                  setMode('plan');
                  setPlanStep(0);
                }}
                disabled={isLoading}
              >
                Plan treningowy
              </Button>
              <Button
                type="button"
                variant={mode === 'quick' ? 'default' : 'outline'}
                onClick={() => setMode('quick')}
                disabled={isLoading}
              >
                Szybki trening
              </Button>
            </div>
          </div>

          {mode === 'plan' && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {[0, 1].map((step) => (
                <div
                  key={step}
                  className={cn(
                    'rounded-full px-2 py-1 border',
                    planStep === step ? 'border-primary text-primary' : 'border-border'
                  )}
                >
                  {PLAN_STEP_LABELS[step as PlanStep]}
                </div>
              ))}
            </div>
          )}

          <FormField
            control={control}
            name="difficulty"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-base">Poziom zaawansowania</FormLabel>
                <FormControl>
                  <Select value={field.value} onValueChange={field.onChange} disabled={isLoading}>
                    <SelectTrigger id="difficulty" className="w-full text-lg">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Novice">Początkujący</SelectItem>
                      <SelectItem value="Intermediate">Średniozaawansowany</SelectItem>
                      <SelectItem value="Advanced">Zaawansowany</SelectItem>
                    </SelectContent>
                  </Select>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {mode === 'plan' && planStep === 0 && (
            <>
              <FormField
                control={control}
                name="age"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-base">Wiek (lata)</FormLabel>
                    <FormControl>
                      <Input
                        id="age"
                        type="number"
                        min={16}
                        max={100}
                        value={field.value}
                        onChange={(event) => field.onChange(event.target.valueAsNumber)}
                        className={cn('text-lg', errors.age && 'border-destructive')}
                        disabled={isLoading}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="space-y-2">
                <Label htmlFor="weight" className="text-base">
                  Waga obecna (kg)
                </Label>
                <Input
                  id="weight"
                  type="number"
                  min={30}
                  max={300}
                  step={0.1}
                  {...register('weight', { valueAsNumber: true })}
                  className={cn('text-lg', errors.weight && 'border-destructive')}
                  disabled={isLoading}
                />
                {errors.weight && <p className="text-sm text-destructive">{errors.weight.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="target_weight" className="text-base">
                  Waga docelowa (kg)
                </Label>
                <Input
                  id="target_weight"
                  type="number"
                  min={30}
                  max={300}
                  step={0.1}
                  {...register('target_weight', { valueAsNumber: true })}
                  className={cn('text-lg', errors.target_weight && 'border-destructive')}
                  disabled={isLoading}
                />
                {errors.target_weight && <p className="text-sm text-destructive">{errors.target_weight.message}</p>}
              </div>
            </>
          )}

          {mode === 'plan' && planStep === 1 && (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="start_date" className="text-base">
                    Data od
                  </Label>
                  <Input
                    id="start_date"
                    type="date"
                    {...register('start_date')}
                    className={cn(errors.start_date && 'border-destructive')}
                    disabled={isLoading}
                  />
                  {errors.start_date && <p className="text-sm text-destructive">{errors.start_date.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date" className="text-base">
                    Data do
                  </Label>
                  <Input
                    id="end_date"
                    type="date"
                    {...register('end_date')}
                    className={cn(errors.end_date && 'border-destructive')}
                    disabled={isLoading}
                  />
                  {errors.end_date && <p className="text-sm text-destructive">{errors.end_date.message}</p>}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="trainings_per_week" className="text-base">
                  Treningów tygodniowo
                </Label>
                <Controller
                  control={control}
                  name="trainings_per_week"
                  render={({ field }) => (
                    <Select
                      value={String(field.value)}
                      onValueChange={(value) => {
                        const nextValue = parseInt(value, 10);
                        field.onChange(nextValue);
                        const selectedDays = (getValues('selected_days') ?? []).slice(0, nextValue);
                        setValue('selected_days', selectedDays, { shouldValidate: true });
                      }}
                      disabled={isLoading}
                    >
                      <SelectTrigger id="trainings_per_week" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 4, 5, 6].map((value) => (
                          <SelectItem key={value} value={String(value)}>
                            {value}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                {errors.trainings_per_week && (
                  <p className="text-sm text-destructive">{errors.trainings_per_week.message}</p>
                )}
              </div>

              <FormField
                control={control}
                name="selected_days"
                render={({ field }) => {
                  const selectedDays = field.value ?? [];
                  const limit = values?.trainings_per_week ?? getValues('trainings_per_week');

                  const toggleDay = (day: DayOfWeek) => {
                    const isSelected = selectedDays.includes(day);
                    let nextSelectedDays: DayOfWeek[];

                    if (isSelected) {
                      nextSelectedDays = selectedDays.filter((selectedDay) => selectedDay !== day);
                    } else {
                      if (selectedDays.length >= limit) {
                        return;
                      }
                      nextSelectedDays = [...selectedDays, day];
                    }

                    field.onChange(nextSelectedDays);
                  };

                  return (
                    <FormItem>
                      <FormLabel className="text-base">
                        Preferowane dni tygodnia (wybierz dokładnie {values?.trainings_per_week ?? getValues('trainings_per_week')})
                      </FormLabel>
                      <FormControl>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {DAY_OPTIONS.map((dayOption) => {
                            const isSelected = selectedDays.includes(dayOption.value);
                            const disabled = !isSelected && selectedDays.length >= limit;
                            return (
                              <Button
                                key={dayOption.value}
                                type="button"
                                variant={isSelected ? 'default' : 'outline'}
                                className="justify-start"
                                onClick={() => toggleDay(dayOption.value)}
                                disabled={isLoading || disabled}
                              >
                                {dayOption.label}
                              </Button>
                            );
                          })}
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  );
                }}
              />
            </>
          )}

          {error && (
            <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <div className="flex items-center justify-between gap-2">
            {mode === 'plan' ? (
              <>
                <Button type="button" variant="outline" onClick={goToPreviousPlanStep} disabled={isLoading || planStep === 0}>
                  Wstecz
                </Button>
                {planStep < 1 ? (
                  <Button type="button" onClick={goToNextPlanStep} disabled={isLoading || !canGoNext}>
                    Dalej
                  </Button>
                ) : (
                  <Button type="button" className="text-lg" disabled={isLoading} onClick={submitPlanFromFinalStep}>
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Generowanie...
                      </>
                    ) : (
                      <>
                        <Dumbbell className="mr-2 h-5 w-5" />
                        Generuj plan treningowy
                      </>
                    )}
                  </Button>
                )}
              </>
            ) : (
              <Button type="button" className="w-full text-lg py-6" disabled={isLoading} onClick={submitQuickMode}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Generowanie...
                  </>
                ) : (
                  <>
                    <Dumbbell className="mr-2 h-5 w-5" />
                    Generuj szybki trening
                  </>
                )}
              </Button>
            )}
          </div>
          </form>
        </Form>
      </CardContent>

      <AlertDialog open={isConflictDialogOpen} onOpenChange={setIsConflictDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Wykryto konflikt terminów</AlertDialogTitle>
            <AlertDialogDescription>
              Dla poniższych dat istnieją już treningi: {pendingConflictDates.join(', ')}.
              Czy chcesz je nadpisać nowym {mode === 'plan' ? 'planem' : 'szybkim treningiem'}?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isLoading}>Anuluj</AlertDialogCancel>
            <AlertDialogAction onClick={handleOverwriteConfirm} disabled={isLoading}>
              Nadpisz
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
