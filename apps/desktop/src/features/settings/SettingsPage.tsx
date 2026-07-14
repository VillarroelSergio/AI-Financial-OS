import { useEffect, useState } from "react";
import { Bot, Copy, Database, HardDrive, Lock, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/ui/Dashboard";
import { updateSetting, type AppSetting } from "@/lib/api/settings";
import { reassignCurrency } from "@/lib/api/transactions";
import { purgeInactiveAccounts } from "@/lib/api/accounts";
import type { AiStatus } from "@/features/assistant/types/aiAssistant.types";
import { createBackup, fetchSecurityStatus, type BackupInfo, type IntegrityCheck, type SecurityStatus } from "@/lib/api/security";
import type { RagDocument } from "@/lib/api/rag";
import { useTheme } from "@/lib/useTheme";
import { loadSettingsOverview } from "./settingsOverview";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSetting[]>([]);
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null);
  const [security, setSecurity] = useState<SecurityStatus | null>(null);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [integrity, setIntegrity] = useState<IntegrityCheck | null>(null);
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [aiError, setAiError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [backupBusy, setBackupBusy] = useState(false);
  const [systemError, setSystemError] = useState<string | null>(null);
  const [currencyFixBusy, setCurrencyFixBusy] = useState(false);
  const [currencyFixMessage, setCurrencyFixMessage] = useState<string | null>(null);
  const [purgeBusy, setPurgeBusy] = useState(false);
  const [purgeMessage, setPurgeMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSettingsOverview()
      .then((overview) => {
        setSettings(overview.settings);
        setAiStatus(overview.aiStatus);
        setAiError(overview.aiError);
        setSecurity(overview.security);
        setBackups(overview.backups);
        setIntegrity(overview.integrity);
        setDocuments(overview.documents);
      })
      .finally(() => setLoading(false));
  }, []);

  const getValue = (key: string): string => {
    const s = settings.find((item) => item.key === key);
    if (!s) return key === "app.language" ? "es" : key === "app.currency" ? "EUR" : "";
    try {
      return JSON.parse(s.value_json) as string;
    } catch {
      return s.value_json;
    }
  };

  const handleUpdate = async (key: string, value: string) => {
    setSaving(key);
    try {
      const updated = await updateSetting(key, JSON.stringify(value));
      setSettings((prev) => prev.map((s) => (s.key === key ? updated : s)));
    } finally {
      setSaving(null);
    }
  };

  const handleBackup = async () => {
    setBackupBusy(true);
    setSystemError(null);
    try {
      const backup = await createBackup();
      setBackups((prev) => [backup, ...prev.filter((item) => item.filename !== backup.filename)]);
      const status = await fetchSecurityStatus();
      setSecurity(status);
    } catch (e) {
      setSystemError(e instanceof Error ? e.message : "No se ha podido crear el backup");
    } finally {
      setBackupBusy(false);
    }
  };

  const handleCurrencyFix = async () => {
    setCurrencyFixBusy(true);
    setCurrencyFixMessage(null);
    try {
      const target = getValue("app.currency") || "EUR";
      const preview = await reassignCurrency("USD", target, true);
      if (!preview.affected) {
        setCurrencyFixMessage("No hay movimientos en USD que corregir.");
        return;
      }
      const ok = window.confirm(
        `Se reasignaran ${preview.affected} movimientos de USD a ${target}. ` +
          "Los importes no cambian de valor, solo la divisa. Se creara un backup previo. ¿Continuar?"
      );
      if (!ok) return;
      const result = await reassignCurrency("USD", target, false);
      setCurrencyFixMessage(`${result.affected} movimientos corregidos a ${target}. Backup: ${result.backup_filename}`);
    } catch (e) {
      setCurrencyFixMessage(e instanceof Error ? e.message : "No se pudo corregir la divisa");
    } finally {
      setCurrencyFixBusy(false);
    }
  };

  const handlePurgeAccounts = async () => {
    setPurgeBusy(true);
    setPurgeMessage(null);
    try {
      const preview = await purgeInactiveAccounts(true);
      if (!preview.affected) {
        setPurgeMessage("No hay cuentas duplicadas inactivas que limpiar.");
        return;
      }
      const ok = window.confirm(
        `Se eliminarán ${preview.affected} cuentas inactivas sin movimientos ni posiciones: ` +
          `${preview.names.join(", ")}. ¿Continuar?`
      );
      if (!ok) return;
      const result = await purgeInactiveAccounts(false);
      setPurgeMessage(`${result.affected} cuentas eliminadas.`);
    } catch (e) {
      setPurgeMessage(e instanceof Error ? e.message : "No se pudo limpiar cuentas");
    } finally {
      setPurgeBusy(false);
    }
  };

  const lastBackup = backups[0];
  const { theme, setTheme } = useTheme();
  const providerStatus = aiStatus?.providers ?? [];

  return (
    <div className="p-8 max-w-[1300px] mx-auto space-y-6" aria-busy={loading}>
      <PageHeader
        eyebrow="Control local"
        title="Ajustes"
        description="Centro de control para idioma, moneda, IA local, datos, privacidad e integridad."
        actions={<span className="rounded-lg border border-hairline-dark bg-accent-teal/10 px-3 py-2 text-xs text-accent-teal">Local-first</span>}
      />

      <div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
        <section className="premium-card rounded-lg overflow-hidden">
          <div className="border-b border-hairline-dark px-5 py-4">
            <h2 className="text-base font-semibold text-on-dark">Preferencias</h2>
            <p className="mt-1 text-xs text-stone">Configuracion visible de la aplicacion.</p>
          </div>
          <div className="divide-y divide-hairline-dark">
            <div className="p-xl flex items-center justify-between gap-6">
              <div><p className="text-body-md text-on-dark">Idioma</p><p className="text-caption text-stone mt-xs">Idioma de la interfaz</p></div>
              <select className="rounded-lg border border-hairline-dark bg-white/[.035] px-md py-sm text-body-sm text-on-dark" value={getValue("app.language")} onChange={(e) => handleUpdate("app.language", e.target.value)} disabled={saving === "app.language"}>
                <option value="es">Espanol</option>
                <option value="en">English</option>
              </select>
            </div>
            <div className="p-xl flex items-center justify-between gap-6">
              <div><p className="text-body-md text-on-dark">Moneda</p><p className="text-caption text-stone mt-xs">Moneda predeterminada</p></div>
              <select className="rounded-lg border border-hairline-dark bg-white/[.035] px-md py-sm text-body-sm text-on-dark" value={getValue("app.currency")} onChange={(e) => handleUpdate("app.currency", e.target.value)} disabled={saving === "app.currency"}>
                <option value="EUR">EUR - Euro</option>
                <option value="USD">USD - Dolar</option>
                <option value="GBP">GBP - Libra</option>
              </select>
            </div>
            <div className="p-xl">
              <p className="text-body-md text-on-dark mb-1">Apariencia</p>
              <p className="text-caption text-stone mb-3">Elige el modo visual de la aplicacion</p>
              <div className="flex gap-3">
                {(["dark", "light"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTheme(t)}
                    className="flex-1 rounded-[28px] p-4 text-left transition-all"
                    style={{
                      border: theme === t ? "2px solid var(--primary)" : "1px solid var(--border-soft)",
                      background: t === "dark" ? "#000000" : "#E4E2DE",
                      cursor: "pointer",
                    }}
                  >
                    <div
                      className="mb-2 h-8 rounded-[10px]"
                      style={{ background: t === "dark" ? "#1d1d1f" : "#EEECE8", border: "1px solid", borderColor: t === "dark" ? "#333336" : "#D2CFC8" }}
                    />
                    <p
                      style={{
                        fontSize: "12px",
                        fontWeight: 600,
                        letterSpacing: "-0.22px",
                        color: t === "dark" ? "#f5f5f7" : "#1d1d1f",
                      }}
                    >
                      {t === "dark" ? "Oscuro" : "Claro"}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="premium-card rounded-lg p-5">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-lg border border-hairline-dark bg-white/[.035] text-primary-bright"><Bot size={18} /></span>
            <div>
              <h2 className="text-base font-semibold text-on-dark">Asistente IA</h2>
              <p className="text-xs text-stone">Preparado para Ollama y LM Studio.</p>
            </div>
          </div>
          <div className="mt-5 grid gap-3">
            {[
              ["Estado asistente", aiStatus?.enabled
                ? (providerStatus.some((p) => p.available) ? "Activo" : "Proveedor offline")
                : aiError ?? "Sin provider activo"],
              ["Proveedor IA", aiStatus?.default_provider
                ? ({ lmstudio: "LM Studio", ollama: "Ollama" }[aiStatus.default_provider.toLowerCase()] ?? aiStatus.default_provider)
                : "No configurado"],
              ["Modelo IA", aiStatus?.default_model ?? "No configurado"],
              ["Ollama", providerStatus.find((p) => p.name.toLowerCase().includes("ollama"))?.available ? "Disponible" : "No disponible"],
              ["LM Studio", providerStatus.find((p) => p.name.toLowerCase().includes("lm"))?.available ? "Disponible" : "No disponible"],
              ["Estado RAG", documents.length > 0 ? "Indexado" : "Sin documentos"],
              ["Documentos indexados", String(documents.length)],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-lg border border-hairline-dark bg-white/[.03] px-3 py-2">
                <span className="text-xs text-stone">{label}</span>
                <span className="text-xs text-on-dark">{value}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <section className="premium-card rounded-lg p-5">
          <ShieldCheck className="text-accent-teal" size={20} />
          <h2 className="mt-3 text-base font-semibold text-on-dark">Privacidad local</h2>
          <p className="mt-2 text-sm leading-6 text-stone">{security?.demo_data_policy ?? "Los datos financieros se procesan localmente. Las funciones externas deben declararse antes de activarse."}</p>
        </section>
        <section className="premium-card rounded-lg p-5">
          <Database className="text-primary-bright" size={20} />
          <h2 className="mt-3 text-base font-semibold text-on-dark">Integridad de base de datos</h2>
          <p className="mt-2 text-sm leading-6 text-stone">{integrity?.database_ok ? `OK - ${integrity.tables.length} tablas verificadas` : "No verificada"}</p>
          {integrity?.issues.length ? <p className="mt-2 text-xs text-accent-danger">{integrity.issues[0]}</p> : null}
        </section>
        <section className="premium-card rounded-lg p-5">
          <HardDrive className="text-accent-warning" size={20} />
          <h2 className="mt-3 text-base font-semibold text-on-dark">Datos locales</h2>
          <p className="mt-2 break-all text-sm leading-6 text-stone">
            {security?.database_filename
              ? `${security.database_filename} en la carpeta de datos del backend (backend/data/)`
              : "No disponible"}
          </p>
          {security?.database_filename && <button onClick={() => navigator.clipboard?.writeText(security.database_filename)} className="mt-3 inline-flex items-center gap-2 rounded-lg border border-hairline-dark px-3 py-2 text-xs text-stone hover:text-on-dark"><Copy size={13} />Copiar nombre</button>}
        </section>
      </div>

      <section className="premium-card rounded-lg p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-on-dark">Backups locales</h2>
            <p className="mt-1 text-sm text-stone">
              {lastBackup
                ? `Ultima copia: ${new Date(lastBackup.created_at).toLocaleString("es-ES")} - ${(lastBackup.size_bytes / 1024).toFixed(1)} KB`
                : "No hay copias registradas todavia."}
            </p>
          </div>
          <button onClick={handleBackup} disabled={backupBusy} className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            {backupBusy ? "Creando..." : "Crear backup"}
          </button>
        </div>
        {systemError && <p className="mt-3 text-sm text-accent-danger">{systemError}</p>}
        <div className="mt-4 grid gap-2">
          {backups.slice(0, 3).map((backup) => (
            <div key={backup.filename} className="flex items-center justify-between gap-3 rounded-lg border border-hairline-dark bg-white/[.03] px-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-xs text-on-dark">{backup.filename}</p>
                <p className="truncate text-[11px] text-stone">{new Date(backup.created_at).toLocaleString("es-ES")}</p>
              </div>
              <span className="financial-number shrink-0 text-xs text-stone">{(backup.size_bytes / 1024).toFixed(1)} KB</span>
            </div>
          ))}
        </div>
      </section>

      <section className="premium-card rounded-lg p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-on-dark">Mantenimiento de datos</h2>
            <p className="mt-1 text-sm text-stone">
              Corrige movimientos importados con divisa USD reasignandolos a la moneda predeterminada. Se muestra un resumen antes de aplicar y se crea un backup.
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCurrencyFix} disabled={currencyFixBusy} className="rounded-lg border border-hairline-dark px-4 py-2 text-sm text-on-dark hover:bg-white/[.05] disabled:opacity-50">
              {currencyFixBusy ? "Comprobando..." : "Corregir divisa USD"}
            </button>
            <button onClick={handlePurgeAccounts} disabled={purgeBusy} className="rounded-lg border border-hairline-dark px-4 py-2 text-sm text-on-dark hover:bg-white/[.05] disabled:opacity-50">
              {purgeBusy ? "Comprobando..." : "Limpiar cuentas duplicadas"}
            </button>
          </div>
        </div>
        {currencyFixMessage && <p className="mt-3 text-sm text-stone">{currencyFixMessage}</p>}
        {purgeMessage && <p className="mt-3 text-sm text-stone">{purgeMessage}</p>}
      </section>

      <section className="premium-card rounded-lg p-5">
        <div className="flex items-start gap-3">
          <Lock size={18} className="mt-0.5 text-accent-teal" />
          <div>
            <h2 className="text-base font-semibold text-on-dark">Datos demo/mock</h2>
            <p className="mt-1 text-sm text-stone">Los estados demo deben identificarse en cada modulo. Esta pantalla queda preparada para exponer el interruptor global cuando exista soporte backend.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
