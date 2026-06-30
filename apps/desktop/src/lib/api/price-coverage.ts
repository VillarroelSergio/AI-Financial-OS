import type { AuditReport, AssetResolutionResponse } from "@/lib/types/price-coverage";
import { api } from "./client";

export const getDefaultAssets = () =>
  api.get<string[]>("/api/investments/price-coverage/default-assets");

export const runAudit = (assets: { name: string }[] = [], forceRefresh = false) =>
  api.post<AuditReport>("/api/investments/price-coverage/audit", {
    assets,
    force_refresh: forceRefresh,
  });

export const resolveAsset = (assetName: string) =>
  api.post<AssetResolutionResponse>("/api/investments/price-coverage/resolve", {
    asset_name: assetName,
  });
