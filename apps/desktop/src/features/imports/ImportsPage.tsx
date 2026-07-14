import { useEffect, useState } from "react";
import { AlertCircle, Check, History, RotateCcw, ShieldCheck, Upload } from "lucide-react";
import { PageHeader } from "@/components/ui/Dashboard";
import { confirmImport, listImports, previewImport, rollbackImport } from "@/lib/api/imports";
import { useAccounts } from "@/lib/hooks/useAccounts";
import type { ImportBatch, ImportPreview } from "@/lib/types";

const steps = ["Archivo y cuenta", "Validacion", "Confirmacion", "Resumen"];
const KNOWN_FORMATS = ["Monefy CSV", "Revolut CSV", "BBVA XLSX", "CSV / Excel generico"];
const demo: ImportPreview = { import_batch_id: "demo", source_type: "revolut", detected_source: "Revolut", columns: ["Fecha de inicio", "Descripción", "Importe"], rows_total: 24, rows_valid: 22, rows_invalid: 1, rows_skipped: 1, warnings_count: 2, mapping: {}, already_imported_at: null, preview_rows: [
  { row_number: 2, date: "2026-06-21", account: "", category: "", amount: "-42.30", currency: "EUR", description: "Mercadona", status: "valid", errors: [], warnings: [] },
  { row_number: 3, date: "2026-06-22", account: "", category: "", amount: "2100.00", currency: "EUR", description: "Nomina", status: "valid", errors: [], warnings: [] },
  { row_number: 4, date: "2026-06-22", account: "", category: "", amount: "-18.00", currency: "EUR", description: "Pago con tarjeta", status: "skipped", errors: ["Operación no completada (REVERTED)"], warnings: [] },
] };

export default function ImportsPage() {
  const demoMode = new URLSearchParams(location.search).get("demo") === "preview";
  const [preview, setPreview] = useState<ImportPreview | null>(demoMode ? demo : null);
  const [step, setStep] = useState(demoMode ? 1 : 0);
  const [history, setHistory] = useState<ImportBatch[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [currencyOverride, setCurrencyOverride] = useState("");
  const [accountId, setAccountId] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | "valid" | "skipped" | "invalid" | "warnings">("");
  const { accounts } = useAccounts();
  const [result, setResult] = useState<{ rows_imported: number; rows_skipped: number; transfers_detected?: number; bills_created?: number } | null>(null);

  const accountName = accounts.find((a) => a.id === accountId)?.name ?? "";

  useEffect(() => { if (!demoMode) listImports().then(setHistory).catch(() => undefined); }, [demoMode]);

  async function chooseFile(file?: File) {
    if (!file) return;
    setBusy(true); setError("");
    try { setPreview(await previewImport(file, "auto")); setStatusFilter(""); setStep(1); }
    catch { setError("No se pudo analizar el archivo. Revisa que sea un CSV (UTF-8) o XLSX valido."); }
    finally { setBusy(false); }
  }

  async function confirm() {
    if (!preview || demoMode) return;
    setBusy(true); setError(""); setStep(2);
    try { setResult(await confirmImport(preview.import_batch_id, preview.mapping, currencyOverride || undefined, accountId)); setStep(3); setHistory(await listImports()); }
    catch { setError("No se pudo completar la importacion. No se han guardado filas nuevas."); setStep(1); }
    finally { setBusy(false); }
  }

  async function rollback(id: string) {
    await rollbackImport(id);
    setHistory(await listImports());
  }

  const statusLabel = (row: ImportPreview["preview_rows"][number]) =>
    row.status === "valid" ? "Valida"
    : row.status === "duplicate" ? "Duplicada"
    : row.status === "skipped" ? (row.errors[0] ?? "Omitida")
    : row.errors[0];

  const toggleFilter = (value: typeof statusFilter) => setStatusFilter((current) => (current === value ? "" : value));
  const visibleRows = (preview?.preview_rows ?? []).filter((row) =>
    statusFilter === "" ? true
    : statusFilter === "warnings" ? row.warnings.length > 0
    : row.status === statusFilter,
  );
  const chipClass = (value: typeof statusFilter, palette: string) =>
    `rounded-lg px-3 py-1.5 transition-colors cursor-pointer ${palette} ${statusFilter === value ? "ring-1 ring-current" : "opacity-80 hover:opacity-100"}`;

  return (
    <div className="page-shell space-y-6">
      <PageHeader
        eyebrow="Datos locales"
        title="Centro de importacion"
        description="Sube el extracto de tu banco en CSV o XLSX. Detectamos el formato, normalizamos fechas e importes y te lo mostramos antes de guardar nada."
        actions={<div className="flex items-center gap-2 text-xs text-stone border border-hairline-dark rounded-lg px-3 py-2 bg-[var(--bg-interactive)]"><ShieldCheck size={15} className="text-accent-teal" />El archivo no sale de tu equipo</div>}
      />

      <div className="premium-card rounded-lg p-5">
        <div className="grid grid-cols-4">{steps.map((label, i) => <div key={label} className="relative"><div className={`h-px absolute top-4 left-0 right-0 ${i <= step ? "bg-primary" : "bg-hairline-dark"}`} /><div className="relative flex flex-col items-center gap-2"><span className={`w-8 h-8 rounded-lg grid place-items-center text-xs border ${i < step ? "bg-primary border-primary text-white" : i === step ? "bg-[var(--bg-interactive)] border-primary-bright text-on-dark" : "bg-surface-deep border-hairline-dark text-stone"}`}>{i < step ? <Check size={14} /> : i + 1}</span><span className="text-xs text-stone">{label}</span></div></div>)}</div>
      </div>

      {error && <div className="flex gap-2 rounded-lg border border-accent-danger/30 bg-accent-danger/10 p-4 text-sm text-accent-danger"><AlertCircle size={18} />{error}</div>}

      {!preview && (
        <section className="premium-card rounded-lg p-7">
          <h2 className="text-lg font-semibold mb-1">1. Cuenta y archivo</h2>
          <p className="text-sm text-stone mb-5">Todos los movimientos del archivo se asignaran a la cuenta que elijas.</p>
          <div className="mb-6 max-w-sm">
            <label className="block text-xs text-stone mb-1.5">Cuenta destino *</label>
            <select value={accountId} onChange={(e) => setAccountId(e.target.value)} className="w-full rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] px-3 py-2.5 text-sm text-on-dark">
              <option value="">Selecciona una cuenta...</option>
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
          <label className={`min-h-40 rounded-lg border border-dashed flex flex-col items-center justify-center bg-black/20 ${accountId ? "border-hairline-dark hover:border-primary cursor-pointer" : "border-hairline-dark opacity-50 cursor-not-allowed"}`}>
            <Upload className="text-primary-bright mb-3" />
            <b>{busy ? "Analizando..." : accountId ? "Arrastra o selecciona un archivo CSV o XLSX" : "Elige primero la cuenta destino"}</b>
            <span className="text-xs text-stone mt-1">Maximo 10 MB - el archivo no sale de tu equipo</span>
            <span className="mt-3 flex flex-wrap gap-2 justify-center">{KNOWN_FORMATS.map((f) => <span key={f} className="rounded-full border border-hairline-dark bg-[var(--bg-interactive)] px-2.5 py-1 text-[11px] text-stone">{f}</span>)}</span>
            <input className="hidden" type="file" accept=".csv,text/csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" disabled={!accountId || busy} onChange={(e) => chooseFile(e.target.files?.[0])} />
          </label>
        </section>
      )}

      {preview && !result && (
        <>
          {preview.already_imported_at && (
            <div className="rounded-lg border border-accent-warning/40 bg-accent-warning/10 p-3">
              <p className="text-body-sm text-accent-warning">
                Este archivo ya se importó el {new Date(preview.already_imported_at).toLocaleDateString("es-ES")}.
                Si continúas, los movimientos ya existentes se marcarán como duplicados.
              </p>
            </div>
          )}
          <section className="premium-card rounded-lg overflow-hidden">
            <div className="p-5 flex flex-wrap items-center gap-3 border-b border-hairline-dark">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-accent-teal/40 bg-accent-teal/10 px-3 py-1 text-xs text-accent-teal"><Check size={12} />Formato detectado: {preview.detected_source ?? "Generico"}</span>
              {(accountName || demoMode) && <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs text-primary-bright">Cuenta: {demoMode ? "BBVA Cuenta corriente" : accountName}</span>}
              <div className="ml-auto flex gap-2 text-xs">
                <button onClick={() => toggleFilter("valid")} className={chipClass("valid", "bg-accent-teal/10 text-accent-teal")}>{preview.rows_valid} validas</button>
                {preview.rows_skipped > 0 && <button onClick={() => toggleFilter("skipped")} className={chipClass("skipped", "bg-[var(--bg-interactive)] text-stone")}>{preview.rows_skipped} omitidas</button>}
                <button onClick={() => toggleFilter("invalid")} className={chipClass("invalid", "bg-accent-danger/10 text-accent-danger")}>{preview.rows_invalid} invalidas</button>
                <button onClick={() => toggleFilter("warnings")} className={chipClass("warnings", "bg-accent-warning/10 text-accent-warning")}>{preview.warnings_count} avisos</button>
              </div>
            </div>
            <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-xs text-stone bg-black/20"><tr>{["Fila", "Fecha", "Categoria", "Descripcion", "Importe", "Estado"].map((x) => <th key={x} className="text-left font-medium px-4 py-3">{x}</th>)}</tr></thead><tbody>{visibleRows.length === 0 ? <tr><td colSpan={6} className="px-4 py-8 text-center text-sm text-stone">No hay filas con este estado en la muestra.</td></tr> : visibleRows.map((row) => <tr key={row.row_number} className="border-t border-divider-soft"><td className="px-4 py-3 text-stone">{row.row_number}</td><td className="px-4 py-3">{row.date}</td><td className="px-4 py-3">{row.category || "-"}</td><td className="px-4 py-3">{row.description}</td><td className={`px-4 py-3 font-medium ${row.status === "skipped" ? "text-stone" : Number(row.amount) < 0 ? "text-accent-danger" : "text-accent-teal"}`}>{row.amount} {row.currency}</td><td className="px-4 py-3"><span className={row.status === "valid" ? "text-accent-teal" : row.status === "skipped" ? "text-stone" : "text-accent-danger"}>{statusLabel(row)}</span></td></tr>)}</tbody></table></div>
          </section>
          <div className="premium-card rounded-lg p-5 flex flex-wrap items-center justify-between gap-4"><div><b>Confirmacion explicita</b><p className="text-sm text-stone mt-1">Solo se guardan filas validas y no duplicadas en <b className="text-on-dark">{demoMode ? "BBVA Cuenta corriente" : accountName}</b>. El lote se puede revertir.</p></div><div className="flex items-center gap-3"><label className="flex items-center gap-2 text-xs text-stone">Divisa<select value={currencyOverride} onChange={(e) => setCurrencyOverride(e.target.value)} className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] px-2 py-2 text-sm text-on-dark"><option value="">Del archivo</option><option value="EUR">EUR</option><option value="USD">USD</option><option value="GBP">GBP</option></select></label><button className="mercury-button px-4 py-2 rounded-lg" onClick={() => { setPreview(null); setStatusFilter(""); setStep(0); }}>Cancelar</button><button disabled={!preview.rows_valid || busy || demoMode} onClick={confirm} className="mercury-button-primary px-5 py-2 rounded-lg disabled:opacity-40">{demoMode ? "Demo de snapshot" : `Importar ${preview.rows_valid} movimientos`}</button></div></div>
        </>
      )}

      {result && <div className="rounded-lg border border-accent-teal/30 bg-accent-teal/10 p-6"><Check className="text-accent-teal mb-3" /><h2 className="text-xl font-semibold">Importacion completada</h2><p className="text-stone mt-2">{result.rows_imported} movimientos guardados en {accountName} - {result.rows_skipped} omitidos.</p>{(result.transfers_detected ?? 0) > 0 && <p className="text-stone mt-1">{result.transfers_detected} traspasos entre cuentas detectados: excluidos de ingresos y gastos.</p>}{(result.bills_created ?? 0) > 0 && <p className="text-stone mt-1">{result.bills_created} facturas registradas automaticamente en Planificacion &gt; Facturas hogar.</p>}<button className="mercury-button px-4 py-2 rounded-lg mt-4" onClick={() => { setPreview(null); setResult(null); setStep(0); }}>Importar otro archivo</button></div>}
      {history.length > 0 && <section><h2 className="flex items-center gap-2 font-semibold mb-4"><History size={18} />Historial</h2><div className="space-y-2">{history.map((item) => <div key={item.id} className="flex items-center justify-between border border-hairline-dark bg-[var(--bg-interactive)] rounded-lg p-4"><div><b>{item.file_name}</b><p className="text-xs text-stone mt-1">{item.source_name} - {item.rows_imported}/{item.rows_total} filas</p></div>{item.status === "imported" && <button onClick={() => rollback(item.id)} className="flex items-center gap-2 text-sm text-accent-danger"><RotateCcw size={14} />Revertir</button>}</div>)}</div></section>}
    </div>
  );
}
