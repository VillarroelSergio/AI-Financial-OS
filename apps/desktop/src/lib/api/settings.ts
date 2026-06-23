import { api } from "./client";

export interface AppSetting {
  id: string;
  key: string;
  value_json: string;
  created_at: string;
  updated_at: string;
}

export const fetchSettings = () => api.get<AppSetting[]>("/api/settings");
export const updateSetting = (key: string, value_json: string) =>
  api.patch<AppSetting>(`/api/settings/${key}`, { value_json });
