// apps/desktop/src/lib/api/market-intelligence.ts
import { api } from "./client";
import type {
  MacroSnapshotMI,
  MarketSnapshotMI,
  ForexSnapshotMI,
  BondSnapshotMI,
  PersonalImpactMI,
  IngestStatus,
} from "@/lib/types/market-intelligence";

export const getMacroSnapshot = () =>
  api.get<MacroSnapshotMI>("/api/market-intelligence/snapshot/macro");

export const getMarketSnapshot = () =>
  api.get<MarketSnapshotMI>("/api/market-intelligence/snapshot/market");

export const getForexSnapshot = () =>
  api.get<ForexSnapshotMI>("/api/market-intelligence/snapshot/forex");

export const getBondSnapshot = () =>
  api.get<BondSnapshotMI>("/api/market-intelligence/snapshot/bonds");

export const getPersonalImpact = () =>
  api.get<PersonalImpactMI>("/api/market-intelligence/personal-impact");

export const getIngestStatus = () =>
  api.get<IngestStatus>("/api/market-intelligence/ingest-status");
