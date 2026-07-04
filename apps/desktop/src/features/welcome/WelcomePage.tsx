import { ArrowRight, BarChart2, Check, LayoutDashboard, PiggyBank, Upload, Wallet } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { useHoldings } from "@/lib/hooks/useInvestments";
import { useSpendingYears } from "@/lib/hooks/useDashboard";
import { markWelcomeSeen } from "./welcomeVersion";

interface Step {
  icon: typeof Wallet;
  title: string;
  guide: string;
  cta: string;
  to: string;
  done: boolean;
}

export default function WelcomePage() {
  const navigate = useNavigate();
  const { accounts } = useAccounts();
  const { holdings } = useHoldings();
  const years = useSpendingYears();

  const hasStocks = holdings.some((h) => h.asset_type === "stock" || h.asset_type === "etf");
  const hasFunds = holdings.some((h) => h.asset_type === "fund" || h.asset_type === "savings_account" || h.asset_type === "cash");

  const steps: Step[] = [
    {
      icon: Wallet,
      title: "1. Crea tus cuentas bancarias",
      guide: "Empieza por tu cuenta corriente y las cuentas donde tengas dinero. Son la base sobre la que se registran movimientos e inversiones.",
      cta: "Crear cuenta",
      to: "/accounts",
      done: accounts.length > 0,
    },
    {
      icon: Upload,
      title: "2. Importa tus movimientos bancarios",
      guide: "Exporta el CSV de tu banco (o de Monefy) e impórtalo. Con los movimientos cargados tendrás gastos, ingresos y ahorro reales.",
      cta: "Importar CSV",
      to: "/imports",
      done: years.length > 0,
    },
    {
      icon: BarChart2,
      title: "3. Da de alta tus acciones",
      guide: "Añade cada acción con su ticker, cantidad y precio de compra. Desde ese momento podrás ver su evolución en Seguimiento de posiciones.",
      cta: "Añadir acción",
      to: "/investments",
      done: hasStocks,
    },
    {
      icon: PiggyBank,
      title: "4. Añade fondos y cuentas de ahorro",
      guide: "Registra tus fondos indexados y cuentas remuneradas para completar tu patrimonio.",
      cta: "Añadir fondo",
      to: "/investments",
      done: hasFunds,
    },
  ];

  const goToDashboard = () => {
    markWelcomeSeen();
    navigate("/");
  };

  const goToStep = (to: string) => {
    markWelcomeSeen();
    navigate(to);
  };

  return (
    <div className="flex flex-col gap-8 p-8 max-w-3xl mx-auto">
      <div>
        <p className="text-xs uppercase tracking-wide text-primary-bright">Guía inicial</p>
        <h1 className="text-2xl font-semibold text-on-dark mt-2">Bienvenido a Financial OS</h1>
        <p className="text-sm text-mute mt-2 leading-relaxed">
          Tu sistema financiero local y privado. Antes de entrar al dashboard, carga tus datos
          básicos en este orden — cada paso se marca como completado automáticamente cuando
          detectamos los datos.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        {steps.map(({ icon: Icon, title, guide, cta, to, done }) => (
          <div
            key={title}
            className={`rounded-xl border p-5 flex items-start gap-4 ${
              done ? "border-emerald-500/30 bg-emerald-500/[.04]" : "border-hairline-dark bg-white/[.02]"
            }`}
          >
            <span
              className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${
                done ? "bg-emerald-500/20 text-emerald-400" : "bg-primary/15 text-primary-bright"
              }`}
            >
              {done ? <Check size={18} /> : <Icon size={18} />}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-on-dark">{title}</p>
              <p className="text-sm text-mute mt-1 leading-relaxed">{guide}</p>
            </div>
            {!done && (
              <button
                onClick={() => goToStep(to)}
                className="shrink-0 flex items-center gap-1.5 rounded-lg border border-hairline-dark px-3 py-2 text-xs text-on-dark hover:border-primary transition-colors"
              >
                {cta}
                <ArrowRight size={12} />
              </button>
            )}
            {done && <span className="shrink-0 text-xs text-emerald-400 py-2">Completado</span>}
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between border-t border-hairline-dark pt-6">
        <p className="text-xs text-mute">
          Puedes volver a esta guía cuando quieras desde la ruta /welcome.
        </p>
        <button
          onClick={goToDashboard}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <LayoutDashboard size={15} />
          Ir al dashboard
        </button>
      </div>
    </div>
  );
}
