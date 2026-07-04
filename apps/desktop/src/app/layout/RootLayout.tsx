import { useEffect, useState } from "react";
import {
  Activity,
  ArrowLeftRight,
  BarChart2,
  Bot,
  Globe,
  LayoutDashboard,
  Settings,
  Sparkles,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { getCopilotContext } from "@/features/assistant/contextualCopilot";
import ComienzaWidget from "./ComienzaWidget";

interface NavItem {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: "/",            icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/finances",    icon: ArrowLeftRight,  label: "Movimientos y cuentas" },
  { to: "/investments", icon: BarChart2,       label: "Inversiones" },
  { to: "/economy",     icon: Globe,           label: "Economía" },
  { to: "/markets",     icon: Activity,        label: "Mercado" },
];

const footItems: NavItem[] = [
  { to: "/assistant", icon: Bot,      label: "Asistente" },
  { to: "/settings",  icon: Settings, label: "Ajustes" },
];

export default function RootLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const copilot = getCopilotContext(location.pathname);
  const showCopilot = location.pathname !== "/assistant" && location.pathname !== "/settings";
  const [copilotOpen, setCopilotOpen] = useState(false);

  useEffect(() => { setCopilotOpen(false); }, [location.pathname]);

  const copilotPopover = copilotOpen && showCopilot ? (
    <div className="absolute right-4 top-12 z-30 w-[344px] rounded-[20px] border border-[var(--border-soft)] bg-[var(--bg-card)] p-5 shadow-2xl">
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
  ) : null;

  return (
    <div className="flex h-full flex-col lg:flex-row" style={{ background: "var(--bg-app)", color: "var(--text-primary)" }} data-app-ready="true">
      {/* Sidebar desktop */}
      <aside className="hidden w-[216px] flex-shrink-0 overflow-y-auto px-3 py-6 lg:flex lg:flex-col" style={{ background: "var(--bg-sidebar)" }}>
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

        {/* key=location.key remonta el widget en cada navegación para refrescar el progreso */}
        <ComienzaWidget key={location.key} />

        <div className="flex-1" />
        <nav aria-label="Navegacion secundaria" className="mt-4 space-y-0.5 border-t border-[var(--border-soft)] pt-3">
          {footItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
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
          {[...navItems, ...footItems].map(({ to, icon: Icon, label, end }) => (
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
          className="relative hidden h-14 shrink-0 items-center justify-between px-6 lg:flex"
          style={{ borderBottom: "1px solid var(--border-soft)", color: "var(--text-secondary)" }}
        >
          <span style={{ fontSize: "17px", lineHeight: "1.21", letterSpacing: "-0.22px" }}>Private command center</span>
          {showCopilot && (
            <button
              onClick={() => setCopilotOpen((open) => !open)}
              aria-label="Copiloto contextual"
              className={`grid h-8 w-8 place-items-center rounded-full transition-colors ${
                copilotOpen
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--text-secondary)] hover:bg-[rgba(245,245,247,0.08)] hover:text-[var(--text-primary)]"
              }`}
            >
              <Sparkles size={15} />
            </button>
          )}
          {copilotPopover}
        </header>
        <div className="flex min-h-0 flex-1">
          <main className="flex-1 min-w-0 overflow-y-auto">
            <Outlet />
          </main>
        </div>
        <div style={{ height: "1px", width: "100%", background: "var(--border-soft)" }} />
      </div>
    </div>
  );
}
