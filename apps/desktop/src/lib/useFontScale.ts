import { useCallback, useState } from "react";

export const FONT_SCALES = {
  compacto: 0.9,
  normal: 1,
  grande: 1.15,
  "muy-grande": 1.3,
} as const;

export type FontScale = keyof typeof FONT_SCALES;

const STORAGE_KEY = "app.font_scale";

export function normalizeFontScale(value: string | null | undefined): FontScale {
  return value && value in FONT_SCALES ? value as FontScale : "normal";
}

export function applyFontScale(value: string | null | undefined) {
  const scale = normalizeFontScale(value);
  document.documentElement.style.setProperty("--font-scale", String(FONT_SCALES[scale]));
  document.documentElement.dataset.fontScale = scale;
}

export function loadStoredFontScale(): FontScale {
  return normalizeFontScale(localStorage.getItem(STORAGE_KEY));
}

export function useFontScale() {
  const [fontScale, setFontScaleState] = useState<FontScale>(() => loadStoredFontScale());

  const setFontScale = useCallback((next: FontScale) => {
    applyFontScale(next);
    localStorage.setItem(STORAGE_KEY, next);
    setFontScaleState(next);
  }, []);

  return { fontScale, setFontScale };
}
