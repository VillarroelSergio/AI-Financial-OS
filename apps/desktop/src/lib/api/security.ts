import { api } from "./client";

export interface SecurityStatus {
  app_env: string;
  database_filename: string;
  backups_available: number;
  encryption_ready: boolean;
  demo_data_policy: string;
}

export interface BackupInfo {
  filename: string;
  size_bytes: number;
  created_at: string;
}

export interface IntegrityCheck {
  status: string;
  database_ok: boolean;
  tables: string[];
  issues: string[];
}

export const fetchSecurityStatus = () => api.get<SecurityStatus>("/api/security/status");
export const fetchBackups = () => api.get<BackupInfo[]>("/api/security/backups");
export const createBackup = () => api.post<BackupInfo>("/api/security/backups", {});
export const fetchIntegrity = () => api.get<IntegrityCheck>("/api/security/integrity");
