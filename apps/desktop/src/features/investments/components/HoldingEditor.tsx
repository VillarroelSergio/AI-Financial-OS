import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Save, X } from "lucide-react";
import type { Account, AssetType, HoldingEnriched } from "@/lib/types";
import { createAsset, createHolding, updateAsset, updateHolding } from "@/lib/api/investments";

const ASSET_TYPES: { value: AssetType; label: string }[] = [
  { value: "stock", label: "Accion" },
  { value: "etf", label: "ETF" },
  { value: "fund", label: "Fondo" },
  { value: "crypto", label: "Cripto" },
  { value: "bond", label: "Bono" },
  { value: "cash", label: "Efectivo" },
  { value: "unknown", label: "Sin clasificar" },
];

interface HoldingEditorProps {
  holding?: HoldingEnriched | null;
  accounts: Account[];
  onClose: () => void;
  onSaved: () => void;
}

export default function HoldingEditor({ holding, accounts, onClose, onSaved }: HoldingEditorProps) {
  const defaultAccount = accounts.find((a) => ["broker", "investment", "savings"].includes(a.type)) ?? accounts[0];
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    account_id: defaultAccount?.id ?? "",
    name: "",
    ticker: "",
    asset_type: "stock" as AssetType,
    quantity: "0",
    average_price: "0",
    current_price: "0",
    currency: "EUR",
    sector: "",
    region: "",
  });

  useEffect(() => {
    if (!holding) return;
    setForm({
      account_id: holding.account_id,
      name: holding.display_name,
      ticker: holding.symbol ?? holding.asset.ticker ?? "",
      asset_type: holding.asset_type,
      quantity: holding.quantity,
      average_price: holding.average_price,
      current_price: holding.current_price ?? "",
      currency: holding.currency,
      sector: holding.asset.sector ?? "",
      region: holding.asset.region ?? "",
    });
  }, [holding]);

  const canSave = useMemo(() => form.account_id && Number(form.quantity) >= 0, [form]);

  const set = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!canSave) return;
    setSaving(true);
    try {
      const assetPayload = {
        name: form.name.trim() || form.ticker.trim() || "Activo sin identificar",
        ticker: form.ticker.trim() || null,
        asset_type: form.asset_type === "cash" ? "savings_account" : form.asset_type,
        currency: form.currency || "EUR",
        sector: form.sector.trim() || null,
        region: form.region.trim() || null,
        price_source: "manual",
      };
      if (holding) {
        await updateAsset(holding.asset_id, assetPayload);
        await updateHolding(holding.id, {
          quantity: form.quantity,
          average_price: form.average_price,
          current_price: form.current_price || undefined,
          current_price_currency: form.currency || "EUR",
        });
      } else {
        const asset = await createAsset(assetPayload);
        await createHolding({
          account_id: form.account_id,
          asset_id: asset.id,
          quantity: form.quantity,
          average_price: form.average_price,
          current_price: form.current_price || undefined,
          current_price_currency: form.currency || "EUR",
        });
      }
      onSaved();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-surface-card border border-hairline-dark rounded-md p-xl space-y-lg">
      <div className="flex items-center justify-between gap-md">
        <h2 className="text-heading-sm text-on-dark">{holding ? "Editar activo" : "Anadir activo"}</h2>
        <button type="button" onClick={onClose} className="text-stone hover:text-on-dark" aria-label="Cerrar">
          <X size={18} />
        </button>
      </div>
      <div className="grid grid-cols-2 gap-md">
        <label className="space-y-xs">
          <span className="text-caption text-stone">Cuenta / broker</span>
          <select className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.account_id} onChange={(e) => set("account_id", e.target.value)} disabled={Boolean(holding)}>
            {accounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
          </select>
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Tipo</span>
          <select className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.asset_type} onChange={(e) => set("asset_type", e.target.value as AssetType)}>
            {ASSET_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
          </select>
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Nombre</span>
          <input className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="Ej. S&P 500 ETF" />
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Ticker / simbolo</span>
          <input className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.ticker} onChange={(e) => set("ticker", e.target.value)} placeholder="Ej. VUSA" />
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Cantidad</span>
          <input type="number" step="0.000001" className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.quantity} onChange={(e) => set("quantity", e.target.value)} />
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Precio medio</span>
          <input type="number" step="0.0001" className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.average_price} onChange={(e) => set("average_price", e.target.value)} />
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Precio actual/manual</span>
          <input type="number" step="0.0001" className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.current_price} onChange={(e) => set("current_price", e.target.value)} />
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Divisa</span>
          <input className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.currency} onChange={(e) => set("currency", e.target.value.toUpperCase())} maxLength={3} />
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Sector</span>
          <input className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.sector} onChange={(e) => set("sector", e.target.value)} placeholder="Opcional" />
        </label>
        <label className="space-y-xs">
          <span className="text-caption text-stone">Region</span>
          <input className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark" value={form.region} onChange={(e) => set("region", e.target.value)} placeholder="Opcional" />
        </label>
      </div>
      <div className="flex justify-end gap-sm">
        <button type="button" onClick={onClose} className="px-lg py-sm text-body-sm text-stone hover:text-on-dark">Cancelar</button>
        <button type="submit" disabled={saving || !canSave} className="inline-flex items-center gap-sm px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright disabled:opacity-50">
          <Save size={15} />
          {saving ? "Guardando..." : "Guardar"}
        </button>
      </div>
    </form>
  );
}
