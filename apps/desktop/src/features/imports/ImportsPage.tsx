import { useEffect, useState } from "react";
import { AlertCircle, Check, FileSpreadsheet, History, RotateCcw, ShieldCheck, Upload } from "lucide-react";
import { confirmImport, listImports, previewImport, rollbackImport } from "@/lib/api/imports";
import type { ImportBatch, ImportPreview } from "@/lib/types";

const steps = ["Fuente", "Archivo", "Preview", "Validación", "Confirmación", "Resumen"];
const demo: ImportPreview = { import_batch_id: "demo", source_type: "monefy", columns: ["date", "account", "category", "amount"], rows_total: 24, rows_valid: 23, rows_invalid: 1, warnings_count: 2, mapping: {}, preview_rows: [
  { row_number: 2, date: "2026-06-21", account: "Efectivo", category: "Alimentación", amount: "-42.30", currency: "EUR", description: "Mercado", status: "valid", errors: [], warnings: [] },
  { row_number: 3, date: "2026-06-22", account: "Banco", category: "Salario", amount: "2100.00", currency: "EUR", description: "Nómina", status: "valid", errors: [], warnings: [] },
  { row_number: 4, date: "31/13/2026", account: "Efectivo", category: "Ocio", amount: "-18.00", currency: "EUR", description: "Cine", status: "invalid", errors: ["Fecha no válida"], warnings: [] },
] };

export default function ImportsPage() {
  const demoMode = new URLSearchParams(location.search).get("demo") === "preview";
  const [source, setSource] = useState<"monefy" | "generic_csv">("monefy");
  const [preview, setPreview] = useState<ImportPreview | null>(demoMode ? demo : null);
  const [step, setStep] = useState(demoMode ? 3 : 0);
  const [history, setHistory] = useState<ImportBatch[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ rows_imported: number; rows_skipped: number } | null>(null);
  useEffect(() => { if (!demoMode) listImports().then(setHistory).catch(() => undefined); }, [demoMode]);

  async function chooseFile(file?: File) {
    if (!file) return;
    setBusy(true); setError(""); setStep(2);
    try { setPreview(await previewImport(file, source)); setStep(3); }
    catch (e) { setError(e instanceof Error ? e.message : "No se pudo analizar el archivo"); setStep(1); }
    finally { setBusy(false); }
  }
  async function confirm() {
    if (!preview || demoMode) return;
    setBusy(true); setError("");
    try { setResult(await confirmImport(preview.import_batch_id, preview.mapping)); setStep(5); setHistory(await listImports()); }
    catch (e) { setError(e instanceof Error ? e.message : "No se pudo importar"); }
    finally { setBusy(false); }
  }
  async function rollback(id: string) { await rollbackImport(id); setHistory(await listImports()); }

  return <div className="p-8 max-w-[1240px] mx-auto">
    <header className="flex items-start justify-between mb-8"><div><p className="text-xs uppercase tracking-[.18em] text-primary-bright mb-2">Datos locales</p><h1 className="text-3xl font-semibold">Centro de importación</h1><p className="text-stone mt-2">Revisa cada movimiento antes de incorporarlo a tus finanzas.</p></div><div className="flex items-center gap-2 text-xs text-stone border border-hairline-dark rounded-full px-3 py-2"><ShieldCheck size={15} className="text-accent-teal"/>El archivo no sale de tu equipo</div></header>
    <div className="grid grid-cols-6 mb-8">{steps.map((label, i) => <div key={label} className="relative"><div className={`h-px absolute top-4 left-0 right-0 ${i <= step ? "bg-primary" : "bg-hairline-dark"}`}/><div className="relative flex flex-col items-center gap-2"><span className={`w-8 h-8 rounded-full grid place-items-center text-xs border ${i < step ? "bg-primary border-primary" : i === step ? "bg-surface-card border-primary-bright" : "bg-surface-deep border-hairline-dark text-stone"}`}>{i < step ? <Check size={14}/> : i + 1}</span><span className="text-xs text-stone">{label}</span></div></div>)}</div>
    {error && <div className="mb-5 flex gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200"><AlertCircle size={18}/>{error}</div>}
    {!preview && <section className="rounded-xl border border-hairline-dark bg-surface-elevated p-7"><h2 className="text-lg font-semibold mb-5">1. Elige el origen</h2><div className="grid grid-cols-2 gap-4 mb-7">{(["monefy", "generic_csv"] as const).map(kind => <button key={kind} onClick={() => {setSource(kind);setStep(1)}} className={`text-left p-5 rounded-lg border ${source === kind ? "border-primary bg-primary/10" : "border-hairline-dark"}`}><FileSpreadsheet className={source === kind ? "text-primary-bright mb-3" : "text-stone mb-3"}/><b>{kind === "monefy" ? "Monefy CSV" : "CSV genérico"}</b><p className="text-sm text-stone mt-1">{kind === "monefy" ? "Mapeo automático de columnas." : "Mapeo flexible de fecha e importe."}</p></button>)}</div><label className="min-h-40 rounded-xl border border-dashed border-hairline-dark hover:border-primary flex flex-col items-center justify-center cursor-pointer bg-black/20"><Upload className="text-primary-bright mb-3"/><b>{busy ? "Analizando…" : "Selecciona un archivo CSV"}</b><span className="text-xs text-stone mt-1">UTF-8 · máximo 10 MB · carga manual</span><input className="hidden" type="file" accept=".csv,text/csv" onChange={e => chooseFile(e.target.files?.[0])}/></label></section>}
    {preview && <><section className="rounded-xl border border-hairline-dark bg-surface-elevated overflow-hidden"><div className="p-5 flex justify-between items-center border-b border-hairline-dark"><div><h2 className="font-semibold">Vista previa y validación</h2><p className="text-sm text-stone mt-1">Hasta 100 filas de {preview.rows_total}.</p></div><div className="flex gap-2 text-xs"><span className="rounded-full bg-emerald-500/10 text-emerald-300 px-3 py-1.5">{preview.rows_valid} válidas</span><span className="rounded-full bg-red-500/10 text-red-300 px-3 py-1.5">{preview.rows_invalid} inválidas</span><span className="rounded-full bg-amber-500/10 text-amber-300 px-3 py-1.5">{preview.warnings_count} avisos</span></div></div><div className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-xs text-stone bg-black/20"><tr>{["Fila","Fecha","Cuenta","Categoría","Descripción","Importe","Estado"].map(x=><th key={x} className="text-left font-medium px-4 py-3">{x}</th>)}</tr></thead><tbody>{preview.preview_rows.map(row=><tr key={row.row_number} className="border-t border-divider-soft"><td className="px-4 py-3 text-stone">{row.row_number}</td><td className="px-4 py-3">{row.date}</td><td className="px-4 py-3">{row.account}</td><td className="px-4 py-3">{row.category || "—"}</td><td className="px-4 py-3">{row.description}</td><td className={`px-4 py-3 font-medium ${Number(row.amount) < 0 ? "text-red-300" : "text-emerald-300"}`}>{row.amount} {row.currency}</td><td className="px-4 py-3"><span className={row.status === "valid" ? "text-emerald-300" : "text-red-300"}>{row.status === "valid" ? "Válida" : row.status === "duplicate" ? "Duplicada" : row.errors[0]}</span></td></tr>)}</tbody></table></div></section><div className="mt-5 rounded-xl border border-hairline-dark bg-surface-elevated p-5 flex items-center justify-between"><div><b>Confirmación explícita</b><p className="text-sm text-stone mt-1">Solo se guardarán filas válidas y no duplicadas. El lote se puede revertir.</p></div><div className="flex gap-3"><button className="px-4 py-2 rounded-lg border border-hairline-dark" onClick={()=>{setPreview(null);setStep(0)}}>Cancelar</button><button disabled={!preview.rows_valid || busy || demoMode} onClick={confirm} className="px-5 py-2 rounded-lg bg-primary disabled:opacity-40">{demoMode ? "Demo de snapshot" : `Importar ${preview.rows_valid} movimientos`}</button></div></div></>}
    {result && <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-6"><Check className="text-emerald-300 mb-3"/><h2 className="text-xl font-semibold">Importación completada</h2><p className="text-stone mt-2">{result.rows_imported} movimientos guardados · {result.rows_skipped} omitidos.</p></div>}
    {history.length > 0 && <section className="mt-8"><h2 className="flex items-center gap-2 font-semibold mb-4"><History size={18}/>Historial</h2><div className="space-y-2">{history.map(item=><div key={item.id} className="flex items-center justify-between border border-hairline-dark bg-surface-elevated rounded-lg p-4"><div><b>{item.file_name}</b><p className="text-xs text-stone mt-1">{item.source_name} · {item.rows_imported}/{item.rows_total} filas</p></div>{item.status === "imported" && <button onClick={()=>rollback(item.id)} className="flex items-center gap-2 text-sm text-red-300"><RotateCcw size={14}/>Revertir</button>}</div>)}</div></section>}
  </div>;
}
