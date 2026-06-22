import {
  Activity,
  ArrowLeftRight,
  BarChart2,
  Bot,
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
  { to: "/insights", icon: Lightbulb, label: "Insights" },
  { to: "/assistant", icon: Bot, label: "Asistente" },
  { to: "/settings", icon: Settings, label: "Ajustes" },
];

export default function RootLayout() {
  return (
    <div className="flex h-full">
      <aside className="w-60 flex-shrink-0 bg-surface-deep border-r border-hairline-dark flex flex-col">
        <div className="h-14 flex items-center px-6 border-b border-hairline-dark">
          <span className="text-heading-sm text-on-dark font-semibold tracking-tight">
            Financial OS
          </span>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 px-3 py-2 rounded-md text-body-sm transition-colors duration-150",
                  isActive
                    ? "bg-surface-elevated text-on-dark"
                    : "text-stone hover:text-on-dark hover:bg-surface-elevated/50",
                ].join(" ")
              }
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto bg-canvas-dark">
        <Outlet />
      </main>
    </div>
  );
}
