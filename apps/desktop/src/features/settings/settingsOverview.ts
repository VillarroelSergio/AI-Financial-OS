import { getAiStatus } from "@/features/assistant/api/aiAssistantApi";
import type { AiStatus } from "@/features/assistant/types/aiAssistant.types";
import { fetchRagDocuments, type RagDocument } from "@/lib/api/rag";
import { fetchBackups, fetchIntegrity, fetchSecurityStatus, type BackupInfo, type IntegrityCheck, type SecurityStatus } from "@/lib/api/security";
import { fetchSettings, type AppSetting } from "@/lib/api/settings";

export interface SettingsOverview {
  settings: AppSetting[];
  aiStatus: AiStatus | null;
  aiError: string | null;
  security: SecurityStatus | null;
  backups: BackupInfo[];
  integrity: IntegrityCheck | null;
  documents: RagDocument[];
}

let overviewPromise: Promise<SettingsOverview> | null = null;

function createSettingsOverview(): Promise<SettingsOverview> {
  return Promise.allSettled([
    fetchSettings(), getAiStatus(), fetchSecurityStatus(), fetchBackups(), fetchIntegrity(), fetchRagDocuments(),
  ]).then(([settings, aiStatus, security, backups, integrity, documents]) => ({
    settings: settings.status === "fulfilled" ? settings.value : [],
    aiStatus: aiStatus.status === "fulfilled" ? aiStatus.value : null,
    aiError: aiStatus.status === "rejected" ? "No disponible" : null,
    security: security.status === "fulfilled" ? security.value : null,
    backups: backups.status === "fulfilled" ? backups.value : [],
    integrity: integrity.status === "fulfilled" ? integrity.value : null,
    documents: documents.status === "fulfilled" ? documents.value : [],
  }));
}

/** La misma promesa se inicia al arrancar y se reutiliza al abrir Ajustes. */
export function preloadSettingsOverview(): Promise<SettingsOverview> {
  return overviewPromise ??= createSettingsOverview();
}

export const loadSettingsOverview = preloadSettingsOverview;
