import { useTheme } from "@/lib/useTheme";

// Paleta de gráficos coherente derivada del azul (Fase 6 · §7.2).
// Fuente única para todos los Recharts.
const LIGHT = ["#0071E3", "#5A9BB8", "#8E8E93", "#2D7B6A", "#B58A2A", "#B34D62"];
const DARK = ["#0A84FF", "#7AB9D1", "#98989D", "#6FC5AE", "#D7AF55", "#F092A3"];

const FINANCIAL_LIGHT = {
  income: "#2D7B6A",
  expense: "#B34D62",
  savings: "#8FA88D",
};

const FINANCIAL_DARK = {
  income: "#6FC5AE",
  expense: "#F092A3",
  savings: "#B4C9AE",
};

export function getChartPalette(theme: "light" | "dark"): string[] {
  return theme === "dark" ? DARK : LIGHT;
}

export function useChartPalette(): string[] {
  const { theme } = useTheme();
  return getChartPalette(theme);
}

export function useFinancialChartColors() {
  const { theme } = useTheme();
  return theme === "dark" ? FINANCIAL_DARK : FINANCIAL_LIGHT;
}
