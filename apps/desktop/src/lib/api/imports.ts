import { api } from "./client";
import type { ImportBatch, ImportPreview } from "@/lib/types";

export function previewImport(file: File, sourceType: string) {
  const form = new FormData();
  form.append("source_type", sourceType);
  form.append("file", file);
  return api.upload<ImportPreview>("/api/imports/preview", form);
}
export const listImports = () => api.get<ImportBatch[]>("/api/imports");
export const confirmImport = (id: string, mapping: Record<string, string>, currencyOverride?: string, accountId?: string) => api.post<{ rows_imported: number; rows_skipped: number; transfers_detected: number; bills_created: number }>(`/api/imports/${id}/confirm`, { mapping, ...(currencyOverride ? { currency_override: currencyOverride } : {}), ...(accountId ? { account_id: accountId } : {}) });
export const rollbackImport = (id: string) => api.post<{ rows_removed: number }>(`/api/imports/${id}/rollback`, {});
