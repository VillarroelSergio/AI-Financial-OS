import { useEffect, useState } from "react";
import Spinner from "@/components/ui/Spinner";
import { fetchSettings, updateSetting, type AppSetting } from "@/lib/api/settings";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings()
      .then(setSettings)
      .finally(() => setLoading(false));
  }, []);

  const getValue = (key: string): string => {
    const s = settings.find((s) => s.key === key);
    if (!s) return "";
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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-2xl space-y-xl max-w-2xl">
      <div>
        <h1 className="text-display-lg text-on-dark">Ajustes</h1>
        <p className="text-body-sm text-stone mt-xs">Configuración de la aplicación</p>
      </div>

      <div className="bg-surface-card border border-hairline-dark rounded-md divide-y divide-hairline-dark">
        <div className="p-xl flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-dark">Idioma</p>
            <p className="text-caption text-stone mt-xs">Idioma de la interfaz</p>
          </div>
          <select
            className="bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
            value={getValue("app.language")}
            onChange={(e) => handleUpdate("app.language", e.target.value)}
            disabled={saving === "app.language"}
          >
            <option value="es">Español</option>
            <option value="en">English</option>
          </select>
        </div>

        <div className="p-xl flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-dark">Moneda</p>
            <p className="text-caption text-stone mt-xs">Moneda predeterminada</p>
          </div>
          <select
            className="bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
            value={getValue("app.currency")}
            onChange={(e) => handleUpdate("app.currency", e.target.value)}
            disabled={saving === "app.currency"}
          >
            <option value="EUR">EUR — Euro</option>
            <option value="USD">USD — Dólar</option>
            <option value="GBP">GBP — Libra</option>
          </select>
        </div>

        <div className="p-xl flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-dark">Tema</p>
            <p className="text-caption text-stone mt-xs">Modo visual de la aplicación</p>
          </div>
          <span className="text-body-sm text-stone">Dark Premium</span>
        </div>
      </div>

      <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
        <p className="text-heading-sm text-on-dark mb-xs">Asistente IA</p>
        <p className="text-body-sm text-stone">
          Disponible en Fase 6. Preparado para Ollama y LM Studio.
        </p>
      </div>
    </div>
  );
}
