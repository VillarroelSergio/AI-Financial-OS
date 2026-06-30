/**
 * Types for the Portfolio Import Assistant.
 *
 * Data-origin model:
 *   captured   – read from screenshot / pasted text
 *   estimated  – calculated (e.g. cost from value + return%)
 *   confirmed  – explicitly verified by the user
 *   provider   – fetched from a market data provider
 *   manual     – user-entered, no auto-update
 */

/** Raw position extracted from pasted broker text (before instrument resolution). */
export interface RawPosition {
  raw_name: string;
  quantity: number | null;
  current_value: number | null;
  current_value_currency: string | null;
  return_pct: number | null;
  raw_text: string;
}

/** Resolution / coverage status codes used server-side. */
export type ResolutionStatus = "resolved" | "ambiguous" | "unavailable";
export type CoverageStatus = "OK" | "FX_PENDING" | "AMBIGUOUS" | "UNAVAILABLE" | "MANUAL" | "ERROR";

/** Import workflow status for a single position. */
export type ImportStatus =
  | "READY"                  // instrument resolved + price available → can import
  | "REQUIRES_CONFIRMATION"  // ambiguous ticker, user must confirm
  | "NO_PRICE"               // instrument found but no price → import as manual
  | "MANUAL"                 // user explicitly marked as manual
  | "REVIEW"                 // some data missing or uncertain
  | "DISCARDED"              // user dismissed this row
  | "IMPORTED"               // successfully imported
  | "ERROR";

/** A position after instrument resolution and price coverage check. */
export interface ValidatedPosition {
  id: string;

  // Captured data
  raw_name: string;
  quantity: number | null;
  current_value: number | null;
  current_value_currency: string | null;
  return_pct: number | null;
  raw_text: string;

  // Estimated (marked as approximate)
  estimated_cost: number | null;
  is_cost_estimated: boolean;

  // Instrument resolution
  selected_ticker: string | null;
  exchange: string | null;
  currency: string | null;
  asset_type: string;
  resolution_status: ResolutionStatus;
  resolution_confidence: number;
  requires_confirmation: boolean;

  // Price coverage
  price: number | null;
  price_currency: string | null;
  eur_price: number | null;
  fx_rate: number | null;
  coverage_status: CoverageStatus | null;

  // Import workflow
  import_status: ImportStatus;
  notes: string[];
}

/** A position with all fields confirmed by the user, ready to create a holding. */
export interface ConfirmPositionIn {
  raw_name: string;
  ticker: string | null;
  exchange: string | null;
  currency: string;
  asset_type: string;
  quantity: number;
  average_price: number;
  current_price: number | null;
  current_price_currency: string;
  price_source: string;
  account_id: string;
  is_manual: boolean;
  is_cost_estimated: boolean;
  notes: string[];
}

/** Result of a single successfully imported holding. */
export interface ImportedHoldingOut {
  holding_id: string;
  asset_id: string;
  raw_name: string;
  ticker: string | null;
  quantity: number;
  average_price: number;
  current_price: number | null;
  account_id: string;
  is_manual: boolean;
}

/** Summary response from the confirm endpoint. */
export interface ConfirmBatchOut {
  imported: ImportedHoldingOut[];
  failed: string[];
  total: number;
  imported_count: number;
}

/** Duplicate check result. */
export interface DuplicateCheckOut {
  ticker: string;
  account_id: string | null;
  duplicate_holding_ids: string[];
  has_duplicates: boolean;
}

/**
 * A row in the review table — extends ValidatedPosition with
 * user-editable overrides before confirmation.
 */
export interface ReviewRow extends ValidatedPosition {
  // User overrides
  override_quantity: number | null;
  override_average_price: number | null;
  override_ticker: string | null;
  override_currency: string | null;
  is_manual: boolean;

  // Duplicate info (populated on demand)
  duplicate_holding_ids: string[];

  /** Local step in the review workflow. */
  review_state:
    | "pending"        // not yet checked
    | "checking"       // validating in progress
    | "ready"          // ready to import
    | "needs_review"   // user must act
    | "imported"       // done
    | "discarded";     // user removed
}
