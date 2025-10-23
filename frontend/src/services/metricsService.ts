import { api } from './authService';

export interface PlanInput {
  classes: { id: number | string; name: string }[];
  slots: { id: number | string; label?: string; start_time?: string; end_time?: string; is_late_slot?: boolean }[];
  assignments: any[];
  people: { id: number | string; name: string; type: string }[];
  expected_projects: { id: number | string; type?: string; title?: string }[];
}

export interface MetricResponse {
  perMetric: Record<string, number>;
  totals: { WeightedTotalScore: number; violations: Record<string, number>; weights: Record<string, number> };
  counts: Record<string, number>;
}

export interface ComparePayload {
  byAlgorithm: Record<string, PlanInput>;
  weights?: Record<string, number>;
  params?: Record<string, any>;
}

export const metricsService = {
  async compute(plan: PlanInput) {
    const res = await api.post<{ success: boolean; metrics: MetricResponse }>('/reports/metrics/compute', plan);
    return res.data.metrics;
  },

  async compare(payload: ComparePayload) {
    const res = await api.post<{ success: boolean; results: { byAlgorithm: Record<string, MetricResponse>; ranking: { algorithm: string; score: number }[] } }>(
      '/reports/metrics/compare',
      payload,
    );
    return res.data.results;
  },
};


