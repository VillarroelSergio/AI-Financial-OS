import {
  Activity,
  ArrowLeftRight,
  BarChart2,
  Bot,
  CalendarDays,
  Globe,
  LayoutDashboard,
  Lightbulb,
  Settings,
  Target,
  TrendingDown,
  Upload,
  Wallet,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

interface NavItem {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: "/", icon: LayoutDashboard, label: "Resumen", end: true },
  { to: "/spending", icon: TrendingDown, label: "Gastos" },
  { to: "/transactions", icon: ArrowLeftRight, label: "Movimientos" },
  { to: "/accounts", icon: Wallet, label: "Cuentas" },
  { to: "/imports", icon: Upload, label: "Importar" },
  { to: "/investments", icon: BarChart2, label: "Inversiones" },
  { to: "/economy", icon: Globe, label: "Economía" },
  { to: "/markets", icon: Activity, label: "Mercados" },
  { to: "/goals", icon: Target, label: "Objetivos" },
  { to: "/planificacion", icon: CalendarDays, label: "Planificación" },
  { to: "/insights", icon: Lightbulb, label: "Insights" },
  { to: "/assistant", icon: Bot, label: "Asistente" },
  { to: "/settings", icon: Settings, label: "Ajustes" },
];

export default function RootLayout() {
  return (
    <div className="flex h-full bg-canvas-dark" data-app-ready="true">
      <aside className="w-[248px] flex-shrink-0 bg-surface-deep border-r border-hairline-dark flex flex-col">
        <div className="h-[72px] flex items-center gap-3 px-5 border-b border-divider-soft">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-sm font-bold">F</span>
          <div><span className="block text-sm text-on-dark font-semibold">Financial OS</span><span className="block text-[10px] text-mute mt-0.5">Private wealth workspace</span></div>
        </div>
        <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto py-5 px-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-body-sm transition-all duration-150",
                  isActive
                    ? "bg-primary/10 text-on-dark shadow-[inset_0_0_0_1px_rgba(91,94,247,.15)] before:absolute before:left-0 before:h-5 before:w-0.5 before:rounded-full before:bg-primary-bright"
                    : "text-stone hover:text-on-dark hover:bg-white/[.035]",
                ].join(" ")
              }
            >
              <Icon size={17} className="shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav><div className="border-t border-divider-soft p-4"><div className="rounded-lg bg-white/[.025] px-3 py-2.5"><p className="text-[11px] font-medium text-on-dark">Datos protegidos</p><p className="text-[10px] text-mute mt-1">Procesamiento local-first</p></div></div>
      </aside>
      <main className="flex-1 min-w-0 overflow-y-auto bg-[radial-gradient(circle_at_65%_-10%,rgba(91,94,247,.08),transparent_35%)]">
        <Outlet />
      </main>
    </div>
  );
}
