import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Upload, Keyboard, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { useAccounts } from "@/lib/hooks/useAccounts";
import type {
  ConfirmPositionIn,
  ConfirmBatchOut,
  ReviewRow,
} from "@/lib/types/portfolio-import";
import {
  parseImportText,
  validateImportBatch,
  confirmImport,
} from "@/lib/api/portfolio-import";

import ImportReviewTable from "./ImportReviewTable";

// ── Step definitions ──────────────────────────────────────────────────────────

type Step = "method" | "input" | "review" | "result";

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeReviewRow(v: ReviewRow): ReviewRow {
  return {
    ...v,
    override_quantity: null,
    override_average_price: null,
    override_ticker: null,
    override_currency: null,
    is_manual: false,
    duplicate_holding_ids: [],
    review_state: "ready",
  };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MethodSelector({ onSelect }: { onSelect: (m: "screenshot" | "manual") => void }) {
  return (
    <div className="flex flex-col gap-3 max-w-lg">
      <div className="grid grid-cols-2 gap-4">
        {/* Screenshot option — disabled until OCR is available */}
        <div className="flex flex-col gap-1">
          <div className="relative">
            <button
              disabled
              className="w-full flex flex-col items-center gap-3 rounded-xl border border-hairline-dark bg-surface-deep px-6 py-8
                opacity-40 cursor-not-allowed text-center"
            >
              <Upload size={28} className="text-stone" />
              <div>
                <p className="font-medium text-on-dark text-sm">Desde captura</p>
                <p className="text-xs text-mute mt-1 leading-snug">
                  Extracción automática desde imagen de pantalla
                </p>
              </div>
            </button>
            <span className="absolute -top-1 -right-1 rounded-full bg-amber-500 px-1.5 py-0.5 text-[9px] font-bold uppercase text-white leading-none">
              Próximo
            </span>
          </div>
          <p className="text-xs text-mute leading-snug px-1">
            La extracción automática desde captura está pendiente. Usa la entrada manual o pega texto.
          </p>
        </div>

        {/* Manual / text-paste option — fully functional */}
        <button
          onClick={() => onSelect("manual")}
          className="flex flex-col items-center gap-3 rounded-xl border border-hairline-dark bg-surface-deep px-6 py-8
            hover:border-primary/40 hover:bg-white/[.03] transition-all text-center group"
        >
          <Keyboard size={28} className="text-stone group-hover:text-on-dark transition-colors" />
          <div>
            <p className="font-medium text-on-dark text-sm">Entrada rápida</p>
            <p className="text-xs text-mute mt-1 leading-snug">
              Introduce posiciones manualmente o pega texto de tu broker
            </p>
          </div>
        </button>
      </div>
    </div>
  );
}

interface ScreenshotInputProps {
  onParsed: (rows: ReviewRow[]) => void;
}

function ScreenshotInput({ onParsed }: ScreenshotInputProps) {
  const [text, setText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleParse = useCallback(async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const raw = await parseImportText(text);
      if (raw.length === 0) {
        setError("No se detectaron posiciones en el texto. Revisa el formato e inténtalo de nuevo.");
        setLoading(false);
        return;
      }
      const validated = await validateImportBatch(raw);
      onParsed(validated.map((v) => makeReviewRow(v as ReviewRow)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al procesar el texto.");
    } finally {
      setLoading(false);
    }
  }, [text, onParsed]);

  return (
    <div className="flex flex-col gap-4 max-w-2xl">
      <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
        <p className="text-sm font-medium text-on-dark">Capturas de cartera</p>
        <p className="mt-1 text-xs leading-5 text-stone">
          Puedes seleccionar una o varias capturas reales. En esta build la extraccion OCR local todavia no esta activada:
          las imagenes no se guardan ni se envian a terceros. Usa el texto copiado como fallback para extraer posiciones.
        </p>
        <label className="mt-3 flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-hairline-dark bg-white/[.03] px-4 py-6 text-center text-sm text-stone hover:border-primary/40 hover:text-on-dark">
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            multiple
            className="hidden"
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          />
          Cargar capturas
        </label>
        {files.length > 0 && (
          <div className="mt-3 rounded-lg border border-amber-400/25 bg-amber-400/10 p-3">
            <p className="text-xs font-medium text-amber-200">{files.length} captura{files.length === 1 ? "" : "s"} seleccionada{files.length === 1 ? "" : "s"}</p>
            <p className="mt-1 text-xs text-stone">OCR local pendiente. No se creara ningun holding desde estas imagenes sin confirmacion ni revision manual.</p>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-hairline-dark bg-surface-deep p-4 text-xs text-stone space-y-1">
        <p className="font-medium text-on-dark mb-2">Fallback de texto pegado (un bloque por posición):</p>
        <pre className="font-mono text-mute leading-relaxed">{`Apple
x 0,564555
140,15 €
+38,76 %

Microsoft
x 1,234
280,50 €
-5,23 %`}</pre>
        <p className="mt-2 text-mute">
          Puedes pegar directamente el texto copiado de tu broker (Trade Republic, Degiro, etc.).
          Los datos extraídos pueden contener errores — revísalos antes de importar.
        </p>
      </div>

      <textarea
        className="h-56 w-full rounded-xl border border-hairline-dark bg-surface-deep px-4 py-3
          text-sm text-on-dark font-mono placeholder:text-mute resize-none
          focus:outline-none focus:border-primary/50 transition-colors"
        placeholder="Pega aquí el texto de tu cartera..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      {error && (
        <p className="text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} />
          {error}
        </p>
      )}

      <button
        onClick={handleParse}
        disabled={loading || !text.trim()}
        className="self-start flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white text-sm font-medium
          hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {loading && <RefreshCw size={14} className="animate-spin" />}
        {loading ? "Procesando..." : "Extraer posiciones"}
      </button>
    </div>
  );
}

interface QuickAddFormProps {
  onAdd: (row: ReviewRow) => void;
}

function QuickAddForm({ onAdd }: QuickAddFormProps) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("");
  const [value, setValue] = useState("");
  const [returnPct, setReturnPct] = useState("");
  const [currency, setCurrency] = useState("EUR");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAdd = useCallback(async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const qtyNum = qty ? parseFloat(qty.replace(",", ".")) : null;
      const valueNum = value ? parseFloat(value.replace(",", ".")) : null;
      const retNum = returnPct ? parseFloat(returnPct.replace(",", ".")) : null;

      const validated = await validateImportBatch([{
        raw_name: name.trim(),
        quantity: qtyNum,
        current_value: valueNum,
        current_value_currency: currency || null,
        return_pct: retNum,
        raw_text: "",
      }]);

      if (validated.length > 0) {
        onAdd(makeReviewRow(validated[0] as ReviewRow));
        setName(""); setQty(""); setValue(""); setReturnPct(""); setCurrency("EUR");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al validar el activo.");
    } finally {
      setLoading(false);
    }
  }, [name, qty, value, returnPct, currency, onAdd]);

  return (
    <div className="flex flex-col gap-4 max-w-2xl">
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="text-xs text-mute mb-1 block">Activo o ticker *</label>
          <input
            className="w-full rounded-lg border border-hairline-dark bg-surface-deep px-3 py-2
              text-sm text-on-dark placeholder:text-mute focus:outline-none focus:border-primary/50"
            placeholder="Apple, AAPL, Iberdrola..."
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
        </div>
        <div>
          <label className="text-xs text-mute mb-1 block">Cantidad</label>
          <input
            className="w-full rounded-lg border border-hairline-dark bg-surface-deep px-3 py-2
              text-sm text-on-dark font-mono placeholder:text-mute focus:outline-none focus:border-primary/50"
            placeholder="0,564555"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-mute mb-1 block">Divisa</label>
          <input
            className="w-full rounded-lg border border-hairline-dark bg-surface-deep px-3 py-2
              text-sm text-on-dark font-mono placeholder:text-mute focus:outline-none focus:border-primary/50"
            placeholder="EUR"
            value={currency}
            onChange={(e) => setCurrency(e.target.value.toUpperCase())}
          />
        </div>
        <div>
          <label className="text-xs text-mute mb-1 block">Valor actual capturado</label>
          <input
            className="w-full rounded-lg border border-hairline-dark bg-surface-deep px-3 py-2
              text-sm text-on-dark font-mono placeholder:text-mute focus:outline-none focus:border-primary/50"
            placeholder="140,15"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-mute mb-1 block">Rentabilidad capturada (%)</label>
          <input
            className="w-full rounded-lg border border-hairline-dark bg-surface-deep px-3 py-2
              text-sm text-on-dark font-mono placeholder:text-mute focus:outline-none focus:border-primary/50"
            placeholder="+38,76"
            value={returnPct}
            onChange={(e) => setReturnPct(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} />
          {error}
        </p>
      )}

      <button
        onClick={handleAdd}
        disabled={loading || !name.trim()}
        className="self-start flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white text-sm font-medium
          hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {loading && <RefreshCw size={14} className="animate-spin" />}
        {loading ? "Validando..." : "Añadir a revisión"}
      </button>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function PortfolioImportPage() {
  const navigate = useNavigate();
  const { accounts } = useAccounts();

  const brokerAccounts = accounts.filter((a) => a.type === "broker" || a.type === "investment");
  const defaultAccountId = brokerAccounts[0]?.id ?? "";

  const [step, setStep] = useState<Step>("method");
  const [method, setMethod] = useState<"screenshot" | "manual" | null>(null);
  const [rows, setRows] = useState<ReviewRow[]>([]);
  const [accountId, setAccountId] = useState(defaultAccountId);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<ConfirmBatchOut | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const handleSelectMethod = (m: "screenshot" | "manual") => {
    setMethod(m);
    setStep("input");
  };

  const handleParsed = (newRows: ReviewRow[]) => {
    setRows(newRows);
    setStep("review");
  };

  const handleAddRow = (row: ReviewRow) => {
    setRows((prev) => {
      const next = [...prev, row];
      setStep("review");
      return next;
    });
  };

  const handleUpdateRow = (id: string, patch: Partial<ReviewRow>) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  };

  const handleDiscard = (id: string) => {
    setRows((prev) =>
      prev.map((r) => (r.id === id ? { ...r, review_state: "discarded" as const } : r))
    );
  };

  const handleMarkManual = (id: string) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, is_manual: true } : r)));
  };

  const readyCount = rows.filter(
    (r) => r.review_state !== "discarded" && (r.is_manual || r.import_status === "READY" || r.import_status === "NO_PRICE")
  ).length;

  const handleConfirm = async () => {
    if (!accountId) return;
    setConfirming(true);
    setConfirmError(null);

    const toImport: ConfirmPositionIn[] = rows
      .filter(
        (r) =>
          r.review_state !== "discarded" &&
          (r.is_manual || r.import_status === "READY" || r.import_status === "NO_PRICE")
      )
      .map((r) => {
        const ticker = r.override_ticker ?? r.selected_ticker ?? null;
        const currency = r.override_currency ?? r.currency ?? "EUR";
        const qty = r.override_quantity ?? r.quantity ?? 0;
        const avgPrice = r.override_average_price ?? r.estimated_cost ?? (r.current_value ?? 0);
        const currentPrice = r.price ?? null;

        return {
          raw_name: r.raw_name,
          ticker,
          exchange: r.exchange ?? null,
          currency,
          asset_type: r.asset_type,
          quantity: qty,
          average_price: avgPrice,
          current_price: currentPrice,
          current_price_currency: r.price_currency ?? currency,
          price_source: r.is_manual ? "manual" : "auto",
          account_id: accountId,
          is_manual: r.is_manual,
          is_cost_estimated: r.is_cost_estimated,
          notes: r.notes,
        };
      });

    try {
      const res = await confirmImport(toImport);
      setResult(res);
      setStep("result");
    } catch (e) {
      setConfirmError(e instanceof Error ? e.message : "Error al importar posiciones.");
    } finally {
      setConfirming(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="p-2xl space-y-xl max-w-screen-xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate("/investments")}
          className="text-stone hover:text-on-dark transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-xl font-semibold text-on-dark">Importar cartera</h1>
          <p className="text-sm text-mute mt-0.5">
            Asistente de importación: entrada manual o texto pegado desde tu broker.
          </p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-xs text-amber-400/80">
        Los datos extraídos desde captura pueden contener errores. Revísalos antes de importar.
        Ningún dato se guardará sin tu confirmación explícita.
      </div>

      {/* Step: Method */}
      {step === "method" && (
        <div className="space-y-4">
          <p className="text-sm text-stone">Elige cómo quieres introducir tus posiciones:</p>
          <MethodSelector onSelect={handleSelectMethod} />
        </div>
      )}

      {/* Step: Input */}
      {step === "input" && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button onClick={() => setStep("method")} className="text-xs text-mute hover:text-stone">
              ← Volver
            </button>
            <p className="text-sm text-stone font-medium">
              {method === "screenshot" ? "Capturas y texto de cartera" : "Entrada rápida manual"}
            </p>
          </div>

          {method === "screenshot" ? (
            <ScreenshotInput onParsed={handleParsed} />
          ) : (
            <QuickAddForm onAdd={handleAddRow} />
          )}

          {/* Show review table if rows already exist (for manual mode) */}
          {rows.length > 0 && method === "manual" && (
            <div className="space-y-3 mt-6">
              <p className="text-sm font-medium text-on-dark">
                Posiciones añadidas ({rows.filter((r) => r.review_state !== "discarded").length})
              </p>
              <ImportReviewTable
                rows={rows}
                accountId={accountId}
                onUpdate={handleUpdateRow}
                onDiscard={handleDiscard}
                onMarkManual={handleMarkManual}
              />
              <button
                onClick={() => setStep("review")}
                className="px-5 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90"
              >
                Revisar y confirmar →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step: Review */}
      {step === "review" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setStep("input")}
                className="text-xs text-mute hover:text-stone"
              >
                ← Añadir más
              </button>
              <p className="text-sm font-medium text-on-dark">
                Revisión de posiciones
              </p>
              <span className="text-xs text-mute">
                ({rows.filter((r) => r.review_state !== "discarded").length} detectadas)
              </span>
            </div>

            {/* Account selector */}
            <div className="flex items-center gap-2">
              <label className="text-xs text-mute">Cuenta destino:</label>
              <select
                className="rounded-lg border border-hairline-dark bg-surface-deep px-3 py-1.5
                  text-xs text-on-dark focus:outline-none focus:border-primary/50"
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
              >
                {brokerAccounts.length === 0 ? (
                  <option value="">Sin cuentas de broker</option>
                ) : (
                  brokerAccounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          <ImportReviewTable
            rows={rows}
            accountId={accountId}
            onUpdate={handleUpdateRow}
            onDiscard={handleDiscard}
            onMarkManual={handleMarkManual}
          />

          {/* Confirm bar */}
          <div className="flex items-center justify-between rounded-xl border border-hairline-dark bg-surface-deep px-5 py-3">
            <div className="text-sm text-stone">
              <span className="text-on-dark font-medium">{readyCount}</span> posiciones listas para importar
              {rows.filter(r => r.import_status === "REQUIRES_CONFIRMATION" && r.review_state !== "discarded").length > 0 && (
                <span className="ml-2 text-amber-400">
                  · {rows.filter(r => r.import_status === "REQUIRES_CONFIRMATION" && r.review_state !== "discarded").length} requieren confirmación
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {confirmError && (
                <p className="text-xs text-red-400 flex items-center gap-1">
                  <AlertCircle size={12} />
                  {confirmError}
                </p>
              )}
              <button
                onClick={handleConfirm}
                disabled={confirming || readyCount === 0 || !accountId}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white text-sm font-medium
                  hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {confirming && <RefreshCw size={14} className="animate-spin" />}
                {confirming ? "Importando..." : `Confirmar importación (${readyCount})`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step: Result */}
      {step === "result" && result && (
        <div className="space-y-6 max-w-lg">
          <div className="flex items-center gap-3">
            <CheckCircle size={24} className="text-emerald-400" />
            <div>
              <p className="font-semibold text-on-dark">Importación completada</p>
              <p className="text-sm text-stone mt-0.5">
                {result.imported_count} de {result.total} posiciones importadas correctamente.
              </p>
            </div>
          </div>

          {/* Summary grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-hairline-dark bg-surface-deep px-5 py-4">
              <p className="text-2xl font-bold text-emerald-400">{result.imported_count}</p>
              <p className="text-xs text-mute mt-1">Posiciones importadas</p>
            </div>
            {result.failed.length > 0 && (
              <div className="rounded-xl border border-hairline-dark bg-surface-deep px-5 py-4">
                <p className="text-2xl font-bold text-red-400">{result.failed.length}</p>
                <p className="text-xs text-mute mt-1">Con error</p>
              </div>
            )}
          </div>

          {result.failed.length > 0 && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 space-y-1">
              <p className="text-xs font-medium text-red-400">Errores:</p>
              {result.failed.map((f, i) => (
                <p key={i} className="text-xs text-red-400/70">{f}</p>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => navigate("/investments")}
              className="px-5 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90"
            >
              Ver cartera →
            </button>
            <button
              onClick={() => {
                setStep("method");
                setRows([]);
                setResult(null);
                setMethod(null);
              }}
              className="px-5 py-2.5 rounded-lg border border-hairline-dark text-sm text-stone hover:text-on-dark"
            >
              Nueva importación
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
