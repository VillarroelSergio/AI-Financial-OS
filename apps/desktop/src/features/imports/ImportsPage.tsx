import { useEffect, useState } from "react";
import { AlertCircle, Check, FileSpreadsheet, History, RotateCcw, ShieldCheck, Upload } from "lucide-react";
import { PageHeader } from "@/components/ui/Dashboard";
import { confirmImport, listImports, previewImport, rollbackImport } from "@/lib/api/imports";
import { useAccounts } from "@/lib/hooks/useAccounts";
import type { ImportBatch, ImportPreview } from "@/lib/types";

const steps = ["Fuente", "Archivo", "Preview", "Validacion", "Confirmacion", "Resumen"];
const demo: ImportPreview = { import_batch_id: "demo", source_type: "monefy", columns: ["date", "account", "category", "amount"], rows_total: 24, rows_valid: 23, rows_invalid: 1, warnings_count: 2, mapping: {}, preview_rows: [
  { row_number: 2, date: "2026-06-21", account: "Efectivo", category: "Alimentacion", amount: "-42.30", currency: "EUR", description: "Mercado", status: "valid", errors: [], warnings: [] },
  { row_number: 3, date: "2026-06-22", account: "Banco", category: "Salario", amount: "2100.00", currency: "EUR", description: "Nomina", status: "valid", errors: [], warnings: [] },
  { row_number: 4, date: "31/13/2026", account: "Efectivo", category: "Ocio", amount: "-18.00", currency: "EUR", description: "Cine", status: "invalid", errors: ["Fecha no valida"], warnings: [] },
] };

export default function ImportsPage() {
  const demoMode = new URLSearchParams(location.search).get("demo") === "preview";
  const [source, setSource] = useState<"monefy" | "generic_csv">("monefy");
  const [preview, setPreview] = useState<ImportPreview | null>(demoMode ? demo : null);
  const [step, setStep] = useState(demoMode ? 3 : 0);
  const [history, setHistory] = useState<ImportBatch[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [currencyOverride, setCurrencyOverride] = useState("");
  const [accountOverride, setAccountOverride] = useState("");
  const { accounts } = useAccounts();
  const [result, setResult] = useState<{ rows_imported: number; rows_skipped: number } | null>(null);

  useEffect(() => { if (!demoMode) listImports().then(setHistory).catch(() => undefined); }, [demoMode]);

  async function chooseFile(file?: File) {
    if (!file) return;
    setBusy(true); setError(""); setStep(2);
    try { setPreview(await previewImport(file, source)); setStep(3); }
    catch { setError("No se pudo analizar el archivo. Revisa formato, columnas y codificacion UTF-8."); setStep(1); }
    finally { setBusy(false); }
  }

  async function confirm() {
    if (!preview || demoMode) return;
    setBusy(true); setError("");
    try { setResult(await confirmImport(preview.import_batch_id, preview.mapping, currencyOverride || undefined, accountOverride || undefined)); setStep(5); setHistory(await listImports()); }
    catch { setError("No se pudo completar la importacion. No se han guardado filas nuevas."); }
    finally { setBusy(false); }
  }

  async function rollback(id: string) {
    await rollbackImport(id);
    setHistory(await listImports());
  }

  return (
    <div className="p-8 max-w-[1300px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Datos locales"
        title="Centro de importacion"
        description="Flujo seguro para revisar, validar y confirmar movimientos antes de incorporarlos a tus finanzas."
        actions={<div className="flex items-center gap-2 text-xs text-stone border border-hairline-dark rounded-lg px-3 py-2 bg-white/[.035]"><ShieldCheck size={15} className="text-accent-teal" />El archivo no sale de tu equipo</div>}
      />

      <div className="premium-card rounded-lg p-5">
        <div className="grid grid-cols-6">{steps.map((label, i) => <div key={label} className="relative"><div className={`h-px absolute top-4 left-0 right-0 ${i <= step ? "bg-primary" : "bg-hairline-dark"}`} /><div className="relative flex flex-col items-center gap-2"><span className={`w-8 h-8 rounded-lg grid place-items-center text-xs border ${i < step ? "bg-primary border-primary text-white" : i === step ? "bg-white/[.06] border-primary-bright text-on-dark" : "bg-surface-deep border-hairline-dark text-stone"}`}>{i < step ? <Check size={14} /> : i + 1}</span><span className="text-xs text-stone">{label}</span></div></div>)}</div>
      </div>

      {error && <div className="flex gap-2 rounded-lg border border-accent-danger/30 bg-accent-danger/10 p-4 text-sm text-accent-danger"><AlertCircle size={18} />{error}</div>}

      {!preview && (
        <section className="premium-card rounded-lg p-7">
          <h2 className="text-lg font-semibold mb-5">1. Elige el origen</h2>
          <div className="grid grid-cols-2 gap-4 mb-7">{(["monefy", "generic_csv"] as const).map((kind) => <button key={kind} onClick={() => { setSource(kind); setStep(1); }} className={`text-left p-5 rounded-lg border transition-colors ${source === kind ? "border-primary bg-primary/10" : "border-hairline-dark bg-white/[.025] hover:bg-white/[.04]"}`}><FileSpreadsheet className={source === kind ? "text-primary-bright mb-3" : "text-stone mb-3"} /><b>{kind === "monefy" ? "Monefy CSV" : "CSV generico"}</b><p className="text-sm text-stone mt-1">{kind === "monefy" ? "Mapeo automatico de columnas." : "Mapeo flexible de fecha e importe."}</p></button>)}</div>
          <label className="min-h-40 rounded-lg border border-dashed border-hairline-dark hover:border-primary flex flex-col items-center justify-center cursor-pointer bg-black/20"><Upload className="text-primary-bright mb-3" /><b>{busy ? "Analizando..." : "Selecciona un archivo CSV o XLSX"}</b><span className="text-xs text-stone mt-1">CSV UTF-8 o Excel - maximo 10 MB - carga manual</span><input className="hidden" type="file" accept=".csv,text/csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(e) => chooseFile(e.target.files?.[0])} /></label>
        </section>
      )}

      {preview && (
        <>
          <section className="premium-card rounded-lg overflow-hidden">
            <div className="p-5 flex justify-between items-center border-b border-hairline-dark"><div><h2 className="font-semibold">Vista previa y validacion</h2><p className="text-sm text-stone mt-1">Hasta 100 filas de {preview.rows_total}.</p></div><div className="flex gap-2 text-xs"><span className="rounded-lg bg-accent-teal/10 text-accent-teal px-3 py-1.5">{preview.rows_valid} validas</span><span className="rounded-lg bg-accent-danger/10 text-accent-danger px-3 py-1.5">{preview.rows_invalid} invalidas</span><span className="rounded-lg bg-accent-warning/10 text-accent-warning px-3 py-1.5">{preview.warnings_count} avisos</span></div></div>
            <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-xs text-stone bg-black/20"><tr>{["Fila", "Fecha", "Cuenta", "Categoria", "Descripcion", "Importe", "Estado"].map((x) => <th key={x} className="text-left font-medium px-4 py-3">{x}</th>)}</tr></thead><tbody>{preview.preview_rows.map((row) => <tr key={row.row_number} className="border-t border-divider-soft"><td className="px-4 py-3 text-stone">{row.row_number}</td><td className="px-4 py-3">{row.date}</td><td className="px-4 py-3">{row.account}</td><td className="px-4 py-3">{row.category || "-"}</td><td className="px-4 py-3">{row.description}</td><td className={`px-4 py-3 font-medium ${Number(row.amount) < 0 ? "text-accent-danger" : "text-accent-teal"}`}>{row.amount} {row.currency}</td><td className="px-4 py-3"><span className={row.status === "valid" ? "text-accent-teal" : "text-accent-danger"}>{row.status === "valid" ? "Valida" : row.status === "duplicate" ? "Duplicada" : row.errors[0]}</span></td></tr>)}</tbody></table></div>
          </section>
          <div className="premium-card rounded-lg p-5 flex items-center justify-between"><div><b>Confirmacion explicita</b><p className="text-sm text-stone mt-1">Solo se guardaran filas validas y no duplicadas. El lote se puede revertir.</p></div><div className="flex items-center gap-3"><label className="flex items-center gap-2 text-xs text-stone">Cuenta<select value={accountOverride} onChange={(e) => setAccountOverride(e.target.value)} className="max-w-44 rounded-lg border border-hairline-dark bg-white/[.035] px-2 py-2 text-sm text-on-dark"><option value="">Del archivo</option>{accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label><label className="flex items-center gap-2 text-xs text-stone">Divisa<select value={currencyOverride} onChange={(e) => setCurrencyOverride(e.target.value)} className="rounded-lg border border-hairline-dark bg-white/[.035] px-2 py-2 text-sm text-on-dark"><option value="">Del archivo</option><option value="EUR">EUR</option><option value="USD">USD</option><option value="GBP">GBP</option></select></label><button className="mercury-button px-4 py-2 rounded-lg" onClick={() => { setPreview(null); setStep(0); }}>Cancelar</button><button disabled={!preview.rows_valid || busy || demoMode} onClick={confirm} className="mercury-button-primary px-5 py-2 rounded-lg disabled:opacity-40">{demoMode ? "Demo de snapshot" : `Importar ${preview.rows_valid} movimientos`}</button></div></div>
        </>
      )}

      {result && <div className="rounded-lg border border-accent-teal/30 bg-accent-teal/10 p-6"><Check className="text-accent-teal mb-3" /><h2 className="text-xl font-semibold">Importacion completada</h2><p className="text-stone mt-2">{result.rows_imported} movimientos guardados - {result.rows_skipped} omitidos.</p></div>}
      {history.length > 0 && <section><h2 className="flex items-center gap-2 font-semibold mb-4"><History size={18} />Historial</h2><div className="space-y-2">{history.map((item) => <div key={item.id} className="flex items-center justify-between border border-hairline-dark bg-white/[.035] rounded-lg p-4"><div><b>{item.file_name}</b><p className="text-xs text-stone mt-1">{item.source_name} - {item.rows_imported}/{item.rows_total} filas</p></div>{item.status === "imported" && <button onClick={() => rollback(item.id)} className="flex items-center gap-2 text-sm text-accent-danger"><RotateCcw size={14} />Revertir</button>}</div>)}</div></section>}
    </div>
  );
}
