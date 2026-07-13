import { useTheme } from "@/lib/useTheme";

// Paleta de gráficos coherente derivada del azul (Fase 6 · §7.2).
// Fuente única para todos los Recharts.
const LIGHT = ["#0071E3", "#5AC8FA", "#8E8E93", "#34C759", "#FF9F0A", "#AF52DE"];
const DARK = ["#0A84FF", "#64D2FF", "#98989D", "#30D158", "#FF9F0A", "#BF5AF2"];

export function getChartPalette(theme: "light" | "dark"): string[] {
  return theme === "dark" ? DARK : LIGHT;
}

export function useChartPalette(): string[] {
  const { theme } = useTheme();
  return getChartPalette(theme);
}
