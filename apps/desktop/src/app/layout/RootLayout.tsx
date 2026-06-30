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
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { getCopilotContext } from "@/features/assistant/contextualCopilot";

interface NavItem {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: "/",             icon: LayoutDashboard, label: "Resumen",      end: true },
  { to: "/spending",     icon: TrendingDown,    label: "Gastos" },
  { to: "/transactions", icon: ArrowLeftRight,  label: "Movimientos" },
  { to: "/accounts",     icon: Wallet,          label: "Cuentas" },
  { to: "/imports",      icon: Upload,          label: "Importar" },
  { to: "/investments",  icon: BarChart2,       label: "Inversiones" },
  { to: "/economy",      icon: Globe,           label: "Economia" },
  { to: "/markets",      icon: Activity,        label: "Mercados" },
  { to: "/goals",        icon: Target,          label: "Objetivos" },
  { to: "/planificacion",icon: CalendarDays,    label: "Planificacion" },
  { to: "/insights",     icon: Lightbulb,       label: "Insights" },
  { to: "/assistant",    icon: Bot,             label: "Asistente" },
  { to: "/settings",     icon: Settings,        label: "Ajustes" },
];

export default function RootLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const copilot = getCopilotContext(location.pathname);
  const showCopilot = location.pathname !== "/assistant" && location.pathname !== "/settings";

  const copilotPanel = showCopilot ? (
    <aside className="hidden w-[344px] shrink-0 overflow-y-auto border-l border-[var(--border-soft)] bg-[var(--bg-app)] p-5 xl:block">
      <div className="sticky top-5 rounded-[28px] border border-[var(--border-soft)] bg-[var(--bg-card)] p-5">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px] bg-[var(--primary)] text-white">
            <Bot size={16} />
          </span>
          <div className="min-w-0">
            <p
              className="font-semibold text-[var(--text-primary)]"
              style={{ fontSize: "14px", lineHeight: "1.43", letterSpacing: "-0.22px" }}
            >
              Copiloto contextual
            </p>
            <p
              className="mt-1 text-[var(--text-secondary)]"
              style={{ fontSize: "12px", lineHeight: "1.43" }}
            >
              {copilot.module} - {copilot.data_status}
            </p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {copilot.visible_metrics.slice(0, 4).map((metric) => (
            <span
              key={metric}
              className="rounded-[10px] border border-[var(--border-soft)] bg-[var(--bg-card-elevated)] px-2 py-1 text-[var(--text-secondary)]"
              style={{ fontSize: "11px" }}
            >
              {metric}
            </span>
          ))}
        </div>
        <div className="mt-3 grid gap-2">
          {copilot.suggestedQuestions.slice(0, 2).map((question) => (
            <button
              key={question}
              onClick={() => navigate("/assistant", { state: { prompt: question, context: copilot } })}
              className="rounded-[10px] border border-[var(--border-soft)] bg-[var(--bg-interactive)] px-3 py-2 text-left text-[var(--text-primary)] hover:border-[var(--border-strong)]"
              style={{ fontSize: "12px", lineHeight: "1.5" }}
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </aside>
  ) : null;

  return (
    <div className="flex h-full flex-col lg:flex-row" style={{ background: "var(--bg-app)", color: "var(--text-primary)" }} data-app-ready="true">
      {/* Sidebar desktop */}
      <aside className="hidden w-[192px] flex-shrink-0 overflow-y-auto px-3 py-6 lg:block" style={{ background: "var(--bg-sidebar)" }}>
        <div className="mb-6 px-3">
          <p
            className="font-semibold text-[var(--color-frost-white)]"
            style={{ fontFamily: "var(--font-sf-pro-display)", fontSize: "19px", lineHeight: "1.21", letterSpacing: "-0.28px" }}
          >
            Financial OS
          </p>
          <p className="mt-1 text-[var(--color-platinum)]" style={{ fontSize: "12px", lineHeight: "1.43" }}>
            Local finance system
          </p>
        </div>

        <nav aria-label="Navegacion principal" className="space-y-0.5">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "flex items-center gap-2.5 rounded-[10px] px-3 py-2.5 transition-colors duration-100",
                  isActive
                    ? "bg-[var(--color-graphite)] text-[var(--color-frost-white)]"
                    : "text-[var(--color-platinum)] hover:bg-[rgba(245,245,247,0.06)] hover:text-[var(--color-frost-white)]",
                ].join(" ")
              }
            >
              <Icon size={14} />
              <span style={{ fontSize: "14px", lineHeight: "1.43", letterSpacing: "-0.22px" }}>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Nav mobile */}
      <div
        className="border-b px-4 py-3 lg:hidden"
        style={{ background: "var(--bg-sidebar)", borderColor: "var(--border-soft)" }}
      >
        <div className="flex items-center justify-between gap-4">
          <div>
            <p
              className="text-[var(--color-frost-white)]"
              style={{ fontFamily: "var(--font-sf-pro-display)", fontSize: "19px", lineHeight: "1.21", letterSpacing: "-0.28px", fontWeight: 600 }}
            >
              Financial OS
            </p>
            <p className="mt-1 text-[var(--color-platinum)]" style={{ fontSize: "12px" }}>
              Local finance system
            </p>
          </div>
          <span className="text-[var(--color-platinum)]" style={{ fontSize: "13px", letterSpacing: "-0.16px" }}>
            Local-first
          </span>
        </div>
        <nav aria-label="Navegacion principal movil" className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "flex min-w-[100px] shrink-0 items-center gap-2 rounded-[10px] border px-3 py-2",
                  isActive
                    ? "border-[var(--color-graphite)] bg-[var(--color-graphite)] text-[var(--color-frost-white)]"
                    : "border-transparent text-[var(--color-platinum)] hover:bg-[rgba(245,245,247,0.06)]",
                ].join(" ")
              }
            >
              <Icon size={13} />
              <span className="truncate" style={{ fontSize: "12px", letterSpacing: "-0.22px" }}>
                {label}
              </span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Contenido principal */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col" style={{ background: "var(--bg-app)" }}>
        <header
          className="hidden h-14 shrink-0 items-center justify-between px-6 lg:flex"
          style={{ borderBottom: "1px solid var(--border-soft)", color: "var(--text-secondary)" }}
        >
          <span style={{ fontSize: "17px", lineHeight: "1.21", letterSpacing: "-0.22px" }}>Private command center</span>
          <span style={{ fontSize: "17px", lineHeight: "1.21", letterSpacing: "-0.22px" }}>Local-first wealth workspace</span>
        </header>
        <div className="flex min-h-0 flex-1">
          <main className="flex-1 min-w-0 overflow-y-auto">
            <Outlet />
          </main>
          {copilotPanel}
        </div>
        <div style={{ height: "1px", width: "100%", background: "var(--border-soft)" }} />
      </div>
    </div>
  );
}
