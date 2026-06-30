import { api } from "./client";

export interface Goal {
  id: string;
  name: string;
  type: "emergency_fund" | "housing" | "investment" | "savings" | "custom";
  target_amount: string;
  current_amount: string;
  target_date: string | null;
  monthly_contribution: string | null;
  priority: "low" | "medium" | "high";
  status: "active" | "completed" | "paused";
  created_at: string;
  updated_at: string;
}

export type GoalCreate = Pick<Goal, "name" | "type" | "target_amount" | "current_amount" | "target_date" | "monthly_contribution" | "priority">;

export const fetchGoals = () => api.get<Goal[]>("/api/goals");
export const createGoal = (data: GoalCreate) => api.post<Goal>("/api/goals", data);
export const updateGoal = (id: string, data: Partial<GoalCreate> & { status?: Goal["status"] }) => api.patch<Goal>(`/api/goals/${id}`, data);
export const deleteGoal = (id: string) => api.delete<void>(`/api/goals/${id}`);

// ── Simulation ────────────────────────────────────────────────────────────────

export interface MonthlyDataPoint {
  month: number;
  label: string;
  conservative: number;
  base: number;
  optimistic: number;
}

export interface ScenarioProjection {
  scenario: "conservative" | "base" | "optimistic";
  label: string;
  color: string;
  annual_growth_rate: number;
  months_to_target: number | null;
  projected_date: string | null;
  achievable_by_target_date: boolean | null;
  final_amount: number;
}

export interface SimulationResult {
  goal_id: string;
  current_amount: number;
  target_amount: number;
  monthly_contribution: number;
  monthly_contribution_needed: number | null;
  inflation_rate: number;
  inflation_adjusted_target: number;
  monthly_data: MonthlyDataPoint[];
  scenarios: ScenarioProjection[];
  target_date: string | null;
  generated_at: string;
}

export interface GoalProgress {
  goal_id: string;
  progress_pct: number;
  remaining: number;
  on_track: boolean | null;
  base_months_to_target: number | null;
  base_projected_date: string | null;
}

export const simulateGoal = (
  id: string,
  params: { inflation_rate?: number; max_months?: number } = {}
) =>
  api.post<SimulationResult>(`/api/goals/${id}/simulate`, {
    inflation_rate: params.inflation_rate ?? 0.03,
    max_months: params.max_months ?? 360,
  });

export const fetchGoalProgress = (id: string) =>
  api.get<GoalProgress>(`/api/goals/${id}/progress`);
