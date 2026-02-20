import axios from 'axios';
import type {
  CreateTrainingRequest,
  CreateQuickTrainingRequest,
  CreateTrainingResponse,
  TaskStatusResponse,
  TrainingPlanResponse,
  TrainingListResponse,
  DashboardStatsResponse,
  TrainingCalendarDaysResponse,
  TrainingConflictsResponse,
  TrainingConflictsRequest,
  QuickTrainingConflictsRequest,
  ExerciseSuggestionsRequest,
  ExerciseSuggestionsResponse,
  ReplaceExerciseRequest,
  ReplaceExerciseResponse,
  TrainingProgressResponse,
  CompleteExerciseRequest,
  ExerciseOpinion,
  MarkExerciseNotCompletedRequest,
  MarkExerciseStatusResponse,
  AuthResponse,
  RefreshResponse,
  User,
} from './types';
import { getAccessToken, setAccessToken, removeAccessToken } from './auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Convert a MuscleWiki video URL to use the backend proxy
 * This is needed because MuscleWiki videos require RapidAPI headers
 */
export function getProxiedVideoUrl(originalUrl: string): string {
  if (!originalUrl) return '';
  return `${API_BASE_URL}/media/video?url=${encodeURIComponent(originalUrl)}`;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send cookies with requests
});

// Request interceptor to add Authorization header
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle 401 errors
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post<RefreshResponse>(
          `${API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const { access_token } = response.data;
        setAccessToken(access_token);
        processQueue(null, access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        removeAccessToken();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const trainingApi = {
  /**
   * Create a new training plan (async operation)
   */
  createTraining: async (data: CreateTrainingRequest): Promise<CreateTrainingResponse> => {
    const response = await apiClient.post<CreateTrainingResponse>('/trainings', data);
    return response.data;
  },

  /**
   * Create a quick one-day training plan (async operation).
   */
  createQuickTraining: async (
    data: CreateQuickTrainingRequest,
    overwriteConflicts: boolean = false
  ): Promise<CreateTrainingResponse> => {
    const response = await apiClient.post<CreateTrainingResponse>('/trainings/quick', data, {
      params: { overwrite_conflicts: overwriteConflicts },
    });
    return response.data;
  },

  /**
   * Get task status by task_id
   */
  getTaskStatus: async (taskId: string): Promise<TaskStatusResponse> => {
    const response = await apiClient.get<TaskStatusResponse>(`/trainings/tasks/${taskId}`);
    return response.data;
  },

  /**
   * Get full training plan by training_id
   */
  getTrainingPlan: async (trainingId: string): Promise<TrainingPlanResponse> => {
    const response = await apiClient.get<TrainingPlanResponse>(`/trainings/${trainingId}`);
    return response.data;
  },

  /**
   * Get list of training plans
   */
  getTrainingsList: async (limit = 10, offset = 0): Promise<TrainingListResponse> => {
    const response = await apiClient.get<TrainingListResponse>('/trainings', {
      params: { limit, offset },
    });
    return response.data;
  },

  /**
   * Get aggregated dashboard stats for selected date window
   */
  getDashboardStats: async (windowDays = 30): Promise<DashboardStatsResponse> => {
    const response = await apiClient.get<DashboardStatsResponse>('/trainings/stats', {
      params: { window_days: windowDays },
    });
    return response.data;
  },

  /**
   * Get flat training calendar day entries
   */
  getTrainingCalendarDays: async (): Promise<TrainingCalendarDaysResponse> => {
    const response = await apiClient.get<TrainingCalendarDaysResponse>('/trainings/days');
    return response.data;
  },

  /**
   * Check conflicts for selected training days in upcoming week
   */
  getTrainingConflicts: async (payload: TrainingConflictsRequest): Promise<TrainingConflictsResponse> => {
    const response = await apiClient.post<TrainingConflictsResponse>('/trainings/conflicts', {
      ...payload,
      selected_days: payload.selected_days,
    });
    return response.data;
  },

  /**
   * Check conflicts for quick training (today only).
   */
  getQuickTrainingConflicts: async (
    payload: QuickTrainingConflictsRequest = {}
  ): Promise<TrainingConflictsResponse> => {
    const response = await apiClient.post<TrainingConflictsResponse>('/trainings/quick/conflicts', payload);
    return response.data;
  },

  /**
   * Get exercise replacement suggestions for one exercise.
   */
  getExerciseSuggestions: async (
    trainingId: string,
    payload: ExerciseSuggestionsRequest
  ): Promise<ExerciseSuggestionsResponse> => {
    const response = await apiClient.post<ExerciseSuggestionsResponse>(
      `/trainings/${trainingId}/exercises/suggestions`,
      payload
    );
    return response.data;
  },

  /**
   * Replace one exercise in a selected training day.
   */
  replaceExercise: async (
    trainingId: string,
    payload: ReplaceExerciseRequest
  ): Promise<ReplaceExerciseResponse> => {
    const response = await apiClient.patch<ReplaceExerciseResponse>(
      `/trainings/${trainingId}/exercises/replace`,
      payload
    );
    return response.data;
  },

  /**
   * Get completion and opinion prefill state for selected training day.
   */
  getTrainingProgress: async (
    trainingId: string,
    day: string
  ): Promise<TrainingProgressResponse> => {
    const response = await apiClient.get<TrainingProgressResponse>(`/trainings/${trainingId}/progress`, {
      params: { day },
    });
    return response.data;
  },

  /**
   * Mark one exercise as completed (one-way action).
   */
  completeExercise: async (
    trainingId: string,
    payload: CompleteExerciseRequest
  ): Promise<MarkExerciseStatusResponse> => {
    const response = await apiClient.post<MarkExerciseStatusResponse>(
      `/trainings/${trainingId}/exercises/complete`,
      payload
    );
    return response.data;
  },

  /**
   * Mark one exercise as not completed with reason.
   */
  markExerciseNotCompleted: async (
    trainingId: string,
    payload: MarkExerciseNotCompletedRequest
  ): Promise<MarkExerciseStatusResponse> => {
    const response = await apiClient.post<MarkExerciseStatusResponse>(
      `/trainings/${trainingId}/exercises/not-completed`,
      payload
    );
    return response.data;
  },
};

export const exerciseOpinionApi = {
  /**
   * Get current user opinion for one exercise.
   */
  getOpinion: async (exerciseId: number): Promise<ExerciseOpinion> => {
    const response = await apiClient.get<ExerciseOpinion>(`/exercise-opinions/${exerciseId}`);
    return response.data;
  },

  /**
   * Upsert current user opinion for one exercise.
   */
  upsertOpinion: async (
    exerciseId: number,
    payload: { rating: number; opinion?: string }
  ): Promise<ExerciseOpinion> => {
    const response = await apiClient.put<ExerciseOpinion>(`/exercise-opinions/${exerciseId}`, payload);
    return response.data;
  },
};

/**
 * Poll task status until completed or failed
 * @param taskId - Task ID to poll
 * @param onProgress - Callback for status updates
 * @param interval - Polling interval in ms (default: 3000)
 * @param maxAttempts - Maximum polling attempts (default: 100)
 */
export async function pollTaskStatus(
  taskId: string,
  onProgress?: (status: TaskStatusResponse) => void,
  interval = 3000,
  maxAttempts = 100
): Promise<TaskStatusResponse> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await trainingApi.getTaskStatus(taskId);

    if (onProgress) {
      onProgress(status);
    }

    if (status.status === 'completed' || status.status === 'failed') {
      return status;
    }

    attempts++;
    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  throw new Error('Przekroczono maksymalny czas oczekiwania na wynik');
}

/**
 * Authentication API
 */
export const authApi = {
  /**
   * Register a new user
   */
  register: async (email: string, password: string, name: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/register', {
      email,
      password,
      name,
    });
    return response.data;
  },

  /**
   * Login with email and password
   */
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  /**
   * Login with Google OAuth
   */
  googleAuth: async (code: string, redirectUri: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/google', {
      code,
      redirect_uri: redirectUri,
    });
    return response.data;
  },

  /**
   * Refresh access token using refresh token (cookie)
   */
  refresh: async (): Promise<RefreshResponse> => {
    const response = await apiClient.post<RefreshResponse>('/auth/refresh');
    return response.data;
  },

  /**
   * Logout (clear refresh token cookie)
   */
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  /**
   * Get current user profile
   */
  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (data: {
    name?: string;
    age?: number;
    weight?: number;
    target_weight?: number;
  }): Promise<User> => {
    const response = await apiClient.patch<User>('/auth/profile', data);
    return response.data;
  },
};
