import { trainingApi } from '@/lib/api-client';
import type {
  DashboardKpis,
  DashboardStatsResponse,
  StatusDistributionPoint,
  TrainingTrendPoint,
  WeekdayDistributionPoint,
} from '@/lib/types';

export type {
  DashboardKpis,
  StatusDistributionPoint,
  TrainingTrendPoint,
  WeekdayDistributionPoint,
};

export type DashboardAnalyticsPayload = DashboardStatsResponse;

export async function getDashboardAnalytics(windowDays = 30): Promise<DashboardAnalyticsPayload> {
  const safeWindowDays = Math.max(1, windowDays);
  return trainingApi.getDashboardStats(safeWindowDays);
}
