import { useEffect, useMemo, useState } from "react";
import { createAccount, fetchAccounts } from "@/lib/api/accounts";
import type { Account } from "@/lib/types";

interface Props {
  accounts: Account[];
  value: string;
  onChange: (accountId: string) => void;
  disabled?: boolean;
}

const inputCls = "w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark";

export default function InvestmentAccountPicker({ accounts, value, onChange, disabled = false }: Props) {
  const [createdAccounts, setCreatedAccounts] = useState<Account[]>([]);
  const [refreshedAccounts, setRefreshedAccounts] = useState<Account[]>([]);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState<"broker" | "investment">("investment");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const available = useMemo(() => {
    const byId = new Map([...accounts, ...refreshedAccounts, ...createdAccounts].map((account) => [account.id, account]));
    return [...byId.values()].filter(
      (account) => ["broker", "investment"].includes(account.type) || account.id === value,
    );
  }, [accounts, createdAccounts, refreshedAccounts, value]);

  useEffect(() => {
    let active = true;
    fetchAccounts()
      .then((items) => { if (active) setRefreshedAccounts(items); })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  const createPortfolio = async (portfolioName: string, portfolioType = type) => {
    const cleanName = portfolioName.trim();
    if (!cleanName) {
      setError("Indica un nombre para la cartera");
      return;
    }
    const existing = available.find(
      (account) => account.name.toLowerCase() === cleanName.toLowerCase(),
    );
    if (existing) {
      onChange(existing.id);
      setCreating(false);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const account = await createAccount({
        name: cleanName,
        type: portfolioType,
        currency: "EUR",
        current_balance: "0.00",
      });
      setCreatedAccounts((current) => [...current, account]);
      onChange(account.id);
      setName("");
      setCreating(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la cartera");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-xs">
      <span className="text-caption text-stone">Cartera / broker</span>
      <select className={inputCls} value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled}>
        <option value="">Selecciona una cartera</option>
        {available.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
      </select>
      {!disabled && (
        <div className="flex flex-wrap gap-sm pt-1">
          <button type="button" onClick={() => setCreating((current) => !current)} className="text-caption text-primary-bright hover:text-primary">
            + Nueva cartera
          </button>
          <button type="button" onClick={() => createPortfolio("Sin cartera asignada", "investment")} disabled={saving} className="text-caption text-stone hover:text-on-dark disabled:opacity-50">
            Usar sin asignar
          </button>
        </div>
      )}
      {creating && (
        <div className="space-y-sm pt-xs">
          <input className={inputCls} value={name} onChange={(event) => setName(event.target.value)} placeholder="Ej. Finizens Global" />
          <div className="flex gap-sm">
            <select className={inputCls} value={type} onChange={(event) => setType(event.target.value as "broker" | "investment")}>
              <option value="investment">Cartera</option>
              <option value="broker">Broker</option>
            </select>
            <button type="button" onClick={() => createPortfolio(name)} disabled={saving} className="mercury-button-primary rounded-sm px-md text-caption disabled:opacity-50">
              {saving ? "Creando" : "Crear"}
            </button>
          </div>
        </div>
      )}
      {error && <p className="text-caption text-accent-danger">{error}</p>}
    </div>
  );
}
