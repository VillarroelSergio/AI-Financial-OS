import type {
  ConfirmBatchOut,
  ConfirmPositionIn,
  DuplicateCheckOut,
  RawPosition,
  ValidatedPosition,
} from "@/lib/types/portfolio-import";
import { api } from "./client";

/** Parse pasted broker text into raw positions (no network calls to market providers). */
export const parseImportText = (text: string) =>
  api.post<RawPosition[]>("/api/investments/import/parse-text", { text });

/** Extract positions from a broker screenshot using the local vision model. */
export function parseImportImage(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api.upload<RawPosition[]>("/api/investments/import/parse-image", form);
}

/** Validate a batch of raw positions: resolve instruments + fetch price coverage. */
export const validateImportBatch = (
  positions: Array<{
    raw_name: string;
    quantity: number | null;
    current_value: number | null;
    current_value_currency: string | null;
    return_pct: number | null;
    raw_text: string;
  }>
) =>
  api.post<ValidatedPosition[]>("/api/investments/import/validate", { positions });

/** Check whether a ticker already has a holding in the given account. */
export const checkDuplicates = (ticker: string, account_id: string | null) =>
  api.post<DuplicateCheckOut>("/api/investments/import/check-duplicates", {
    ticker,
    account_id,
  });

/** Create holdings from explicitly confirmed positions. */
export const confirmImport = (positions: ConfirmPositionIn[]) =>
  api.post<ConfirmBatchOut>("/api/investments/import/confirm", { positions });
