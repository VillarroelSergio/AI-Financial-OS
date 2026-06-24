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
