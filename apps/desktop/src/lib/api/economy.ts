import type { EconomicIndicator, MacroSnapshot, PersonalImpact } from "@/lib/types";
import { api } from "./client";

export const getSnapshot = () =>
  api.get<MacroSnapshot>("/api/economy/snapshot");

export const getIndicators = (region?: string, indicator?: string) => {
  const params = new URLSearchParams();
  if (region) params.set("region", region);
  if (indicator) params.set("indicator", indicator);
  const qs = params.toString();
  return api.get<EconomicIndicator[]>(`/api/economy/indicators${qs ? `?${qs}` : ""}`);
};

export const refreshEconomy = () =>
  api.post<MacroSnapshot>("/api/economy/refresh", {});

export const getPersonalImpact = () =>
  api.get<PersonalImpact>("/api/economy/impact");
