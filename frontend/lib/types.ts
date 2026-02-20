// API Types matching backend schemas

export type DayOfWeek =
  | 'monday'
  | 'tuesday'
  | 'wednesday'
  | 'thursday'
  | 'friday'
  | 'saturday'
  | 'sunday';

export interface CreateTrainingRequest {
  age?: number; // Age (16-100)
  weight?: number; // Current weight kg (30-300)
  target_weight?: number; // Target weight kg (30-300)
  difficulty?: 'Novice' | 'Intermediate' | 'Advanced';
  start_date?: string;
  end_date?: string;
  trainings_per_week?: number;
  selected_days?: DayOfWeek[]; // Selected training days (1-6)
  overwrite_conflicts?: boolean;
  conflict_dates?: string[];
}

export interface CreateQuickTrainingRequest {
  difficulty?: 'Novice' | 'Intermediate' | 'Advanced';
}

export interface CreateTrainingResponse {
  task_id: string;
  status: string;
  message: string;
  check_status_url: string;
}

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface TaskStatusResponse {
  task_id: string;
  status: TaskStatus;
  message: string;
  result?: {
    training_id: string;
    schema_version?: number;
  };
  error?: string;
  created_at?: string;
  completed_at?: string;
}

export interface Video {
  url: string;
  angle?: string;
}

export interface Exercise {
  name: string;
  exercise_id?: number;
  primary_muscles?: string[];
  difficulty?: string;
  category?: string;
  videos: Video[];
  repetitions: string;
  steps: string[];
}

export interface TrainingDay {
  day: string; // ISO date string
  name: string;
  timeRequired: number; // Minutes
  bodyParts?: string[];
  exercises: Exercise[];
}

export interface TrainingPlanResponse {
  id: string;
  trainings: TrainingDay[];
  created_at: string;
}

export type ExerciseSuggestionMode = 'ai' | 'manual';

export interface ExerciseSuggestionItem {
  exercise_id: number;
  name: string;
  primary_muscles: string[];
  difficulty?: string;
  category?: string;
  videos: Video[];
  repetitions: string;
  steps: string[];
}

export interface ExerciseSuggestionsRequest {
  day: string;
  exercise_index: number;
  mode: ExerciseSuggestionMode;
  query?: string;
  limit?: number;
  refresh_seed?: number;
}

export interface ExerciseSuggestionsResponse {
  mode: ExerciseSuggestionMode;
  context_source: 'exercise_primary_muscles' | 'training_day_body_parts' | 'random_top';
  fallback_used: boolean;
  suggestions: ExerciseSuggestionItem[];
}

export interface ReplaceExerciseRequest {
  day: string;
  exercise_index: number;
  replacement_exercise_id: number;
}

export interface ReplaceExerciseResponse {
  training_id: string;
  day: string;
  exercise_index: number;
  exercise: Exercise;
  timeRequired: number;
  updated_at: string;
}

export interface ExerciseOpinion {
  exercise_id: number;
  rating: number;
  opinion: string;
  updated_at: string;
}

export interface TrainingProgressResponse {
  day: string;
  is_trackable_today: boolean;
  completed_exercise_indices: number[];
  not_completed_exercise_indices: number[];
  not_completed_reasons_by_exercise_index: Record<
    string,
    { reason_code: NotCompletedReasonCode; reason_text: string }
  >;
  opinions_by_exercise_id: Record<string, ExerciseOpinion>;
}

export interface CompleteExerciseRequest {
  day: string;
  exercise_index: number;
}

export interface CompleteExerciseResponse {
  training_id: string;
  day: string;
  exercise_index: number;
  exercise_id: number;
  status: 'completed' | 'not_completed';
  reason_code: NotCompletedReasonCode | null;
  reason_text: string | null;
  updated_at: string;
  completed_at: string | null;
  existing_opinion: ExerciseOpinion | null;
}

export type NotCompletedReasonCode =
  | 'brak_czasu'
  | 'zbyt_trudne'
  | 'bol_dyskomfort'
  | 'brak_sprzetu'
  | 'brak_motywacji'
  | 'inne';

export interface MarkExerciseNotCompletedRequest {
  day: string;
  exercise_index: number;
  reason_code: NotCompletedReasonCode;
  reason_text?: string;
}

export interface MarkExerciseStatusResponse {
  training_id: string;
  day: string;
  exercise_index: number;
  exercise_id: number;
  status: 'completed' | 'not_completed';
  reason_code: NotCompletedReasonCode | null;
  reason_text: string | null;
  updated_at: string;
  completed_at: string | null;
  existing_opinion: ExerciseOpinion | null;
}

export interface TrainingListItem {
  id: string;
  created_at: string;
  difficulty?: string;
  training_dates: string[];
  trainings_count: number;
}

export interface TrainingListResponse {
  total: number;
  trainings: TrainingListItem[];
}

export interface TrainingCalendarDayItem {
  date: string;
  training_id: string;
  training_name: string;
}

export interface TrainingCalendarDaysResponse {
  days: TrainingCalendarDayItem[];
}

export interface DashboardKpis {
  scheduled_trainings: number;
  completed_exercises_percent: number;
  not_completed_exercises: number;
  most_active_weekday: string;
}

export interface TrainingTrendPoint {
  date: string;
  count: number;
}

export interface StatusDistributionPoint {
  status: 'completed' | 'not_completed' | 'pending';
  value: number;
}

export interface WeekdayDistributionPoint {
  weekday: string;
  count: number;
}

export interface DashboardStatsResponse {
  kpis: DashboardKpis;
  training_trend: TrainingTrendPoint[];
  status_distribution: StatusDistributionPoint[];
  weekday_distribution: WeekdayDistributionPoint[];
}

export interface TrainingConflictItem {
  date: string;
  existing_training_id: string;
  existing_training_name: string;
}

export interface TrainingConflictsResponse {
  has_conflicts: boolean;
  conflict_dates: string[];
  conflicts: TrainingConflictItem[];
}

export interface TrainingConflictsRequest {
  start_date?: string;
  end_date?: string;
  trainings_per_week?: number;
  selected_days: DayOfWeek[];
}

export interface QuickTrainingConflictsRequest {
  timezone?: string;
}

// Auth Types

export interface UserProfile {
  age: number | null;
  weight: number | null;
  target_weight: number | null;
}

export interface User {
  id: string;
  email: string;
  name: string;
  profile: UserProfile;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}
