'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Angry,
  Check,
  CheckCircle,
  Frown,
  Laugh,
  Loader2,
  Meh,
  PlayCircle,
  Smile,
  Sparkles,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type {
  Exercise,
  ExerciseOpinion,
  ExerciseSuggestionItem,
  NotCompletedReasonCode,
} from '@/lib/types';
import { exerciseOpinionApi, getProxiedVideoUrl, trainingApi } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface ExerciseItemProps {
  trainingId?: string;
  trainingDay: string;
  exercise: Exercise;
  exerciseIndex: number;
  exerciseNumber: number;
  isCompleted?: boolean;
  isNotCompleted?: boolean;
  notCompletedReason?: { reason_code: NotCompletedReasonCode; reason_text: string };
  prefilledOpinion?: ExerciseOpinion;
  onExerciseReplaced?: (payload: {
    day: string;
    exerciseIndex: number;
    exercise: Exercise;
    timeRequired: number;
  }) => void;
}

export default function ExerciseItem({
  trainingId,
  trainingDay,
  exercise,
  exerciseIndex,
  exerciseNumber,
  isCompleted = false,
  isNotCompleted = false,
  notCompletedReason,
  prefilledOpinion,
  onExerciseReplaced,
}: ExerciseItemProps) {
  const reasonOptions: { value: NotCompletedReasonCode; label: string }[] = [
    { value: 'brak_czasu', label: 'Brak czasu' },
    { value: 'zbyt_trudne', label: 'Zbyt trudne' },
    { value: 'bol_dyskomfort', label: 'Ból / dyskomfort' },
    { value: 'brak_sprzetu', label: 'Brak sprzętu' },
    { value: 'brak_motywacji', label: 'Brak motywacji' },
    { value: 'inne', label: 'Inne' },
  ];

  const ratingOptions = [
    { value: 1, Icon: Angry, className: 'text-red-600 bg-red-100 border-red-300' },
    { value: 2, Icon: Frown, className: 'text-orange-600 bg-orange-100 border-orange-300' },
    { value: 3, Icon: Meh, className: 'text-amber-600 bg-amber-100 border-amber-300' },
    { value: 4, Icon: Smile, className: 'text-lime-600 bg-lime-100 border-lime-300' },
    { value: 5, Icon: Laugh, className: 'text-green-600 bg-green-100 border-green-300' },
  ] as const;

  const [manualQuery, setManualQuery] = useState('');
  const [isManualOpen, setIsManualOpen] = useState(false);
  const [isLoadingManual, setIsLoadingManual] = useState(false);
  const [manualSuggestions, setManualSuggestions] = useState<ExerciseSuggestionItem[]>([]);
  const [manualHint, setManualHint] = useState<string | null>(null);

  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [isLoadingAi, setIsLoadingAi] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<ExerciseSuggestionItem[]>([]);
  const [selectedAiExerciseId, setSelectedAiExerciseId] = useState<number | null>(null);
  const [aiHint, setAiHint] = useState<string | null>(null);

  const [isReplacing, setIsReplacing] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [isSavingOpinion, setIsSavingOpinion] = useState(false);
  const [isNotCompleting, setIsNotCompleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [completedState, setCompletedState] = useState(isCompleted);
  const [notCompletedState, setNotCompletedState] = useState(isNotCompleted);
  const [isNotCompletedModalOpen, setIsNotCompletedModalOpen] = useState(false);
  const [reasonCode, setReasonCode] = useState<NotCompletedReasonCode>(
    notCompletedReason?.reason_code ?? 'brak_czasu'
  );
  const [reasonText, setReasonText] = useState(notCompletedReason?.reason_text ?? '');
  const [rating, setRating] = useState(prefilledOpinion?.rating ?? 3);
  const [opinionText, setOpinionText] = useState(prefilledOpinion?.opinion ?? '');
  const [lastSavedRating, setLastSavedRating] = useState(prefilledOpinion?.rating ?? 3);
  const [lastSavedOpinion, setLastSavedOpinion] = useState(prefilledOpinion?.opinion ?? '');

  const manualQueryNormalized = useMemo(() => manualQuery.trim(), [manualQuery]);
  const hasTrackableTarget = Boolean(trainingId && typeof exercise.exercise_id === 'number');
  const isTrackableExercise = hasTrackableTarget;
  const isFinalized = completedState || notCompletedState;
  const reasonLabel = useMemo(
    () => reasonOptions.find((item) => item.value === reasonCode)?.label ?? 'Inne',
    [reasonCode]
  );

  const fetchManualSuggestions = useCallback(
    async (query?: string) => {
      if (!trainingId) {
        return;
      }
      try {
        setIsLoadingManual(true);
        setErrorMessage(null);
        const response = await trainingApi.getExerciseSuggestions(trainingId, {
          day: trainingDay,
          exercise_index: exerciseIndex,
          mode: 'manual',
          query: query || undefined,
          limit: 20,
        });
        setManualSuggestions(response.suggestions);
        setManualHint(
          response.context_source === 'random_top'
            ? 'Pokazujemy ogólne propozycje, bo brakuje danych mięśniowych.'
            : null
        );
      } catch (error) {
        console.error('Failed to fetch manual suggestions', error);
        setErrorMessage('Nie udało się pobrać propozycji manualnych.');
        setManualSuggestions([]);
      } finally {
        setIsLoadingManual(false);
      }
    },
    [exerciseIndex, trainingDay, trainingId]
  );

  const fetchAiSuggestions = useCallback(async (forceRefresh: boolean = false) => {
    if (!trainingId) {
      return;
    }

    if (!forceRefresh && aiSuggestions.length > 0) {
      return;
    }

    setIsLoadingAi(true);
    setErrorMessage(null);
    if (forceRefresh) {
      setAiSuggestions([]);
      setSelectedAiExerciseId(null);
    }

    try {
      const response = await trainingApi.getExerciseSuggestions(trainingId, {
        day: trainingDay,
        exercise_index: exerciseIndex,
        mode: 'ai',
        limit: 3,
        refresh_seed: Date.now(),
      });
      setAiSuggestions(response.suggestions);
      setSelectedAiExerciseId(response.suggestions[0]?.exercise_id ?? null);
      setAiHint(
        response.context_source === 'random_top'
          ? 'Pokazujemy ogólne propozycje, bo brakuje danych mięśniowych.'
          : null
      );
    } catch (error) {
      console.error('Failed to fetch AI suggestions', error);
      setErrorMessage('Nie udało się pobrać propozycji AI.');
      setAiSuggestions([]);
      setSelectedAiExerciseId(null);
    } finally {
      setIsLoadingAi(false);
    }
  }, [aiSuggestions.length, exerciseIndex, trainingDay, trainingId]);

  const openAiModal = useCallback(async () => {
    setIsAiModalOpen(true);
    await fetchAiSuggestions(false);
  }, [fetchAiSuggestions]);

  const handleReplace = useCallback(
    async (replacementExerciseId: number) => {
      if (!trainingId || !onExerciseReplaced) {
        return;
      }
      try {
        setIsReplacing(true);
        setErrorMessage(null);
        const response = await trainingApi.replaceExercise(trainingId, {
          day: trainingDay,
          exercise_index: exerciseIndex,
          replacement_exercise_id: replacementExerciseId,
        });
        onExerciseReplaced({
          day: response.day,
          exerciseIndex: response.exercise_index,
          exercise: response.exercise,
          timeRequired: response.timeRequired,
        });

        setIsManualOpen(false);
        setManualSuggestions([]);
        setIsAiModalOpen(false);
        setAiSuggestions([]);
      } catch (error) {
        console.error('Failed to replace exercise', error);
        setErrorMessage('Nie udało się podmienić ćwiczenia.');
      } finally {
        setIsReplacing(false);
      }
    },
    [exerciseIndex, onExerciseReplaced, trainingDay, trainingId]
  );

  useEffect(() => {
    if (!isManualOpen) {
      return;
    }
    const timer = setTimeout(() => {
      fetchManualSuggestions(manualQueryNormalized);
    }, 350);
    return () => clearTimeout(timer);
  }, [fetchManualSuggestions, isManualOpen, manualQueryNormalized]);

  useEffect(() => {
    setIsManualOpen(false);
    setManualSuggestions([]);
    setIsAiModalOpen(false);
    setAiSuggestions([]);
    setSelectedAiExerciseId(null);
  }, [exercise.exercise_id, exercise.name]);

  useEffect(() => {
    setCompletedState(isCompleted);
  }, [isCompleted]);

  useEffect(() => {
    setNotCompletedState(isNotCompleted);
  }, [isNotCompleted]);

  useEffect(() => {
    setReasonCode(notCompletedReason?.reason_code ?? 'brak_czasu');
    setReasonText(notCompletedReason?.reason_text ?? '');
  }, [notCompletedReason?.reason_code, notCompletedReason?.reason_text]);

  useEffect(() => {
    setRating(prefilledOpinion?.rating ?? 3);
    setOpinionText(prefilledOpinion?.opinion ?? '');
    setLastSavedRating(prefilledOpinion?.rating ?? 3);
    setLastSavedOpinion(prefilledOpinion?.opinion ?? '');
  }, [prefilledOpinion?.rating, prefilledOpinion?.opinion]);

  const persistOpinion = useCallback(async (
    nextRating: number,
    nextOpinion: string,
  ): Promise<boolean> => {
    if (typeof exercise.exercise_id !== 'number') {
      return false;
    }

    try {
      setIsSavingOpinion(true);
      setErrorMessage(null);
      await exerciseOpinionApi.upsertOpinion(exercise.exercise_id, {
        rating: nextRating,
        opinion: nextOpinion,
      });
      setLastSavedRating(nextRating);
      setLastSavedOpinion(nextOpinion);
      return true;
    } catch (error) {
      console.error('Failed to save opinion', error);
      setErrorMessage('Nie udało się zapisać opinii.');
      return false;
    } finally {
      setIsSavingOpinion(false);
    }
  }, [exercise.exercise_id]);

  const handleCompleteExercise = useCallback(async () => {
    if (!trainingId || !isTrackableExercise || isFinalized) {
      return;
    }
    try {
      setIsCompleting(true);
      setErrorMessage(null);
      const response = await trainingApi.completeExercise(trainingId, {
        day: trainingDay,
        exercise_index: exerciseIndex,
      });
      setCompletedState(true);
      setNotCompletedState(false);
      if (response.existing_opinion) {
        setRating(response.existing_opinion.rating);
        setOpinionText(response.existing_opinion.opinion ?? '');
        setLastSavedRating(response.existing_opinion.rating);
        setLastSavedOpinion(response.existing_opinion.opinion ?? '');
      }
    } catch (error) {
      console.error('Failed to complete exercise', error);
      setErrorMessage('Nie udało się zapisać wykonania ćwiczenia.');
    } finally {
      setIsCompleting(false);
    }
  }, [exerciseIndex, isFinalized, isTrackableExercise, trainingDay, trainingId]);

  const handleNotCompletedSubmit = useCallback(async () => {
    if (!trainingId || !isTrackableExercise || isFinalized) {
      return;
    }
    try {
      setIsNotCompleting(true);
      setErrorMessage(null);
      const response = await trainingApi.markExerciseNotCompleted(trainingId, {
        day: trainingDay,
        exercise_index: exerciseIndex,
        reason_code: reasonCode,
        reason_text: reasonText.trim(),
      });
      setReasonCode(response.reason_code ?? reasonCode);
      setReasonText(response.reason_text ?? '');
      setNotCompletedState(true);
      setCompletedState(false);
      setIsNotCompletedModalOpen(false);
    } catch (error) {
      console.error('Failed to mark exercise as not completed', error);
      setErrorMessage('Nie udało się zapisać statusu niewykonania.');
    } finally {
      setIsNotCompleting(false);
    }
  }, [exerciseIndex, isFinalized, isTrackableExercise, reasonCode, reasonText, trainingDay, trainingId]);

  const handleRatingChange = useCallback(async (nextRating: number) => {
    setRating(nextRating);
    if (!completedState) {
      return;
    }
    if (nextRating === lastSavedRating && opinionText === lastSavedOpinion) {
      return;
    }
    await persistOpinion(nextRating, opinionText);
  }, [completedState, lastSavedOpinion, lastSavedRating, opinionText, persistOpinion]);

  const handleOpinionBlur = useCallback(async () => {
    if (!completedState) {
      return;
    }
    if (rating === lastSavedRating && opinionText === lastSavedOpinion) {
      return;
    }
    await persistOpinion(rating, opinionText);
  }, [completedState, lastSavedOpinion, lastSavedRating, opinionText, persistOpinion, rating]);

  return (
    <AccordionItem value={`exercise-${exerciseNumber}`} className="border-b">
      <AccordionTrigger className="hover:no-underline py-4">
        <div className="flex items-start gap-3 text-left">
          {completedState ? (
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-700 border border-green-300 flex-shrink-0">
              <Check className="h-4 w-4" />
            </div>
          ) : notCompletedState ? (
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 text-orange-700 border border-orange-300 flex-shrink-0">
              <X className="h-4 w-4" />
            </div>
          ) : (
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm flex-shrink-0">
              {exerciseNumber}
            </div>
          )}
          <div className="space-y-1 flex-1">
            <p className="font-semibold text-base leading-tight">{exercise.name}</p>
            <p className="text-sm text-muted-foreground flex items-center gap-1">
              <CheckCircle className="h-3 w-3" />
              {exercise.repetitions}
            </p>
            {notCompletedState && (
              <p className="text-xs text-orange-700">
                Niewykonane: {reasonLabel}
                {reasonText ? ` - ${reasonText}` : ''}
              </p>
            )}
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="pb-4">
        <div className="space-y-4 pl-11">
          {exercise.videos.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium flex items-center gap-2">
                <PlayCircle className="h-4 w-4" />
                Wideo instruktażowe
              </p>
              <div className="grid gap-3">
                {exercise.videos.map((video, idx) => {
                  const videoKey = `${exercise.exercise_id ?? exercise.name}-${video.url}-${idx}`;
                  return (
                    <div key={videoKey} className="space-y-1">
                      <video
                        key={`video-${videoKey}`}
                        controls
                        className="w-full rounded-lg border border-border"
                        preload="metadata"
                      >
                        <source key={`source-${videoKey}`} src={getProxiedVideoUrl(video.url)} type="video/mp4" />
                        Twoja przeglądarka nie obsługuje odtwarzania wideo.
                      </video>
                      {video.angle && (
                        <p className="text-xs text-muted-foreground capitalize">
                          Kąt: {video.angle}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {exercise.steps.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">Instrukcja wykonania</p>
              <ol className="space-y-2 list-decimal list-inside text-sm text-muted-foreground">
                {exercise.steps.map((step, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {trainingId && (
            <div className="space-y-3">
              {hasTrackableTarget && (
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={completedState ? 'secondary' : 'default'}
                    size="sm"
                    disabled={isFinalized || isCompleting || isReplacing || !isTrackableExercise}
                    onClick={handleCompleteExercise}
                  >
                    {isCompleting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Zapisywanie...
                      </>
                    ) : completedState ? (
                      'Wykonane'
                    ) : (
                      'Ćwiczenie wykonane'
                    )}
                  </Button>
                  <Button
                    variant={notCompletedState ? 'secondary' : 'outline'}
                    size="sm"
                    disabled={isFinalized || isNotCompleting || isReplacing || !isTrackableExercise}
                    onClick={() => setIsNotCompletedModalOpen(true)}
                  >
                    {isNotCompleting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Zapisywanie...
                      </>
                    ) : notCompletedState ? (
                      'Niewykonane'
                    ) : (
                      'Ćwiczenie niewykonane'
                    )}
                  </Button>
                </div>
              )}

              {onExerciseReplaced && (
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={isLoadingManual || isReplacing || isCompleting}
                    onClick={() => {
                      const next = !isManualOpen;
                      setIsManualOpen(next);
                      if (next) {
                        fetchManualSuggestions(manualQueryNormalized);
                      }
                    }}
                  >
                    Wybierz manualnie
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-violet-600 text-violet-700 hover:bg-violet-50"
                    disabled={isLoadingAi || isReplacing || isCompleting}
                    onClick={() => {
                      openAiModal();
                    }}
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    {isLoadingAi ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Ładowanie AI...
                      </>
                    ) : (
                      'Wybierz z AI'
                    )}
                  </Button>
                </div>
              )}

              {completedState && typeof exercise.exercise_id === 'number' && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Opinia po ćwiczeniu</p>
                  <p className="text-xs text-muted-foreground">Jak oceniasz to ćwiczenie?</p>
                  <div className="flex flex-wrap gap-2">
                    {ratingOptions.map((option) => {
                      const selected = rating === option.value;
                      const Icon = option.Icon;
                      return (
                        <label
                          key={option.value}
                          aria-label={`Ocena ${option.value}`}
                          className={cn(
                            'inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border transition-all',
                            option.className,
                            selected ? 'ring-2 ring-primary ring-offset-1' : 'opacity-75 hover:opacity-100',
                            isSavingOpinion && 'cursor-not-allowed opacity-50'
                          )}
                        >
                          <input
                            type="radio"
                            className="sr-only"
                            name={`rating-${exerciseNumber}`}
                            value={option.value}
                            checked={selected}
                            onChange={() => {
                              void handleRatingChange(option.value);
                            }}
                            disabled={isSavingOpinion}
                          />
                          <Icon className="h-5 w-5" />
                        </label>
                      );
                    })}
                  </div>
                  <label htmlFor={`opinion-${exerciseNumber}`} className="text-xs text-muted-foreground">
                    Opinia
                  </label>
                  <textarea
                    id={`opinion-${exerciseNumber}`}
                    value={opinionText}
                    onChange={(event) => setOpinionText(event.target.value)}
                    onBlur={() => {
                      void handleOpinionBlur();
                    }}
                    maxLength={500}
                    disabled={isSavingOpinion}
                    className="w-full min-h-20 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    placeholder="Jak oceniasz to ćwiczenie?"
                  />
                </div>
              )}

              {isManualOpen && (
                <div className="space-y-2">
                  <Input
                    value={manualQuery}
                    onChange={(event) => setManualQuery(event.target.value)}
                    placeholder="Szukaj ćwiczenia..."
                    disabled={isLoadingManual || isReplacing}
                  />
                  {manualHint && <p className="text-xs text-muted-foreground">{manualHint}</p>}
                  {isLoadingManual ? (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Pobieranie propozycji...
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-52 overflow-y-auto">
                      {manualSuggestions.map((item) => (
                        <button
                          type="button"
                          key={item.exercise_id}
                          onClick={() => handleReplace(item.exercise_id)}
                          disabled={isReplacing}
                          className="w-full text-left border rounded-md p-2 hover:bg-accent transition-colors disabled:opacity-60"
                        >
                          <p className="text-sm font-medium">{item.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {item.primary_muscles.join(', ') || 'Brak danych mięśni'}
                          </p>
                        </button>
                      ))}
                      {manualSuggestions.length === 0 && (
                        <p className="text-xs text-muted-foreground">
                          Brak dostępnych propozycji dla tego ćwiczenia.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {errorMessage && <p className="text-xs text-destructive">{errorMessage}</p>}
            </div>
          )}
        </div>

        <AlertDialog open={isAiModalOpen} onOpenChange={setIsAiModalOpen}>
          <AlertDialogContent className="w-[96vw] max-w-[96vw] data-[size=default]:sm:max-w-6xl max-h-[78vh] grid-rows-[auto_1fr_auto]">
            <AlertDialogHeader className="place-items-start text-left">
              <AlertDialogTitle>Wybierz ćwiczenie z AI</AlertDialogTitle>
            </AlertDialogHeader>

            {isLoadingAi ? (
              <div className="py-8 flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                AI przygotowuje propozycje...
              </div>
            ) : (
              <div className="space-y-5 h-full min-h-0 overflow-hidden">
                {aiHint && <p className="text-xs text-muted-foreground">{aiHint}</p>}
                <div className="grid gap-5 h-full min-h-0 overflow-y-auto pb-8 pr-1 md:grid-cols-3 items-start content-start">
                  {aiSuggestions.map((item) => {
                    const selected = selectedAiExerciseId === item.exercise_id;
                    const frontalVideo =
                      item.videos.find((video) => (video.angle || '').toLowerCase() === 'front') ||
                      item.videos[0];
                    return (
                      <button
                        key={item.exercise_id}
                        type="button"
                        onClick={() => setSelectedAiExerciseId(item.exercise_id)}
                        className={cn(
                          'text-left border rounded-lg p-3 transition-all flex flex-col justify-start self-start',
                          selected
                            ? 'border-primary bg-primary/5 shadow-lg opacity-100'
                            : 'hover:bg-accent opacity-70'
                        )}
                      >
                        <p className="font-semibold text-sm">{item.name}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Mięśnie: {item.primary_muscles.join(', ') || 'Brak danych'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Poziom: {item.difficulty || 'Brak'} | Kategoria: {item.category || 'Brak'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Powtórzenia: {item.repetitions}
                        </p>
                        {frontalVideo?.url && (
                          <video
                            autoPlay
                            loop
                            muted
                            playsInline
                            className="w-full rounded-md border border-border mt-2 aspect-video object-cover"
                            preload="metadata"
                          >
                            <source src={getProxiedVideoUrl(frontalVideo.url)} type="video/mp4" />
                            Twoja przeglądarka nie obsługuje odtwarzania wideo.
                          </video>
                        )}
                        {item.steps.length > 0 && (
                          <p className="text-xs text-muted-foreground mt-2 line-clamp-3">
                            {item.steps.join(' ')}
                          </p>
                        )}
                      </button>
                    );
                  })}
                  {aiSuggestions.length === 0 && (
                    <p className="text-xs text-muted-foreground">Brak propozycji AI dla tego ćwiczenia.</p>
                  )}
                </div>
              </div>
            )}

            <AlertDialogFooter className="pt-3 bg-background relative z-10">
              <Button
                type="button"
                variant="outline"
                className="border-violet-600 text-violet-700 hover:bg-violet-50"
                disabled={isReplacing || isLoadingAi}
                onClick={() => fetchAiSuggestions(true)}
              >
                {isLoadingAi ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generowanie...
                  </>
                ) : (
                  'Zaproponuj nowe'
                )}
              </Button>
              <AlertDialogCancel disabled={isReplacing}>Anuluj</AlertDialogCancel>
              <Button
                type="button"
                disabled={!selectedAiExerciseId || isReplacing || isLoadingAi}
                onClick={() => {
                  if (selectedAiExerciseId) {
                    handleReplace(selectedAiExerciseId);
                  }
                }}
              >
                {isReplacing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Podmienianie...
                  </>
                ) : (
                  'Zamień ćwiczenie'
                )}
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <AlertDialog open={isNotCompletedModalOpen} onOpenChange={setIsNotCompletedModalOpen}>
          <AlertDialogContent className="max-w-lg">
            <AlertDialogHeader className="place-items-start text-left">
              <AlertDialogTitle>Dlaczego ćwiczenie nie zostało wykonane?</AlertDialogTitle>
            </AlertDialogHeader>

            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {reasonOptions.map((option) => {
                  const selected = reasonCode === option.value;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      className={cn(
                        'rounded-md border px-3 py-2 text-left text-sm transition-colors',
                        selected ? 'border-primary bg-primary/10' : 'hover:bg-accent'
                      )}
                      onClick={() => setReasonCode(option.value)}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>

              <textarea
                value={reasonText}
                onChange={(event) => setReasonText(event.target.value)}
                maxLength={500}
                className="w-full min-h-24 rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Opcjonalny komentarz"
              />
            </div>

            <AlertDialogFooter>
              <AlertDialogCancel disabled={isNotCompleting}>Anuluj</AlertDialogCancel>
              <Button type="button" disabled={isNotCompleting} onClick={() => void handleNotCompletedSubmit()}>
                {isNotCompleting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Zapisywanie...
                  </>
                ) : (
                  'Zapisz'
                )}
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </AccordionContent>
    </AccordionItem>
  );
}
