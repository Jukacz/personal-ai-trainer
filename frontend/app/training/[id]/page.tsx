import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import type { TrainingPlanResponse } from '@/lib/types';
import { TrainingPlanClient } from '@/components/training/training-plan-client';

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  await params;
  return {
    title: `Plan Treningowy - AI Personal Trainer`,
    description: `Szczegóły planu treningowego`,
  };
}

async function fetchTrainingPlan(trainingId: string, accessToken: string | undefined): Promise<TrainingPlanResponse | null> {
  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(`${API_BASE_URL}/trainings/${trainingId}`, {
      headers,
      cache: 'no-store', // Always fetch fresh data
    });

    if (!response.ok) {
      console.error('Failed to fetch training plan:', response.status);
      return null;
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching training plan:', error);
    return null;
  }
}

export default async function TrainingPlanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: trainingId } = await params;
  const cookieStore = await cookies();
  const accessToken = cookieStore.get('access_token')?.value;

  const trainingPlan = await fetchTrainingPlan(trainingId, accessToken);
  const error = !trainingPlan ? 'Nie udało się pobrać planu treningowego' : null;

  return <TrainingPlanClient trainingPlan={trainingPlan} error={error} />;
}
