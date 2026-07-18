import type { LucideIcon } from "lucide-react";
import {
  Briefcase,
  Car,
  CircleEllipsis,
  Dumbbell,
  Gamepad2,
  Gift,
  HeartPulse,
  House,
  Landmark,
  PawPrint,
  PiggyBank,
  Shirt,
  ShoppingCart,
  Smartphone,
  Tag,
  Utensils,
} from "lucide-react";
import type { Category } from "@/lib/types";

export interface CategoryVisual {
  name: string;
  type?: Category["type"];
  icon?: string | null;
  color?: string | null;
}

const DEFAULT_ACCENT = "#8D969E";

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  briefcase: Briefcase,
  car: Car,
  "circle-ellipsis": CircleEllipsis,
  dumbbell: Dumbbell,
  "gamepad-2": Gamepad2,
  gift: Gift,
  "heart-pulse": HeartPulse,
  home: House,
  house: House,
  landmark: Landmark,
  "paw-print": PawPrint,
  "piggy-bank": PiggyBank,
  shirt: Shirt,
  "shopping-cart": ShoppingCart,
  smartphone: Smartphone,
  tag: Tag,
  utensils: Utensils,
};

const ICON_BY_CATEGORY_NAME: Record<string, keyof typeof CATEGORY_ICONS> = {
  ahorros: "piggy-bank",
  alimentacion: "shopping-cart",
  casa: "home",
  comida: "shopping-cart",
  comunicaciones: "smartphone",
  depositos: "landmark",
  deportes: "dumbbell",
  entretenimiento: "gamepad-2",
  mascotas: "paw-print",
  nomina: "briefcase",
  ocio: "gamepad-2",
  regalos: "gift",
  restaurante: "utensils",
  ropa: "shirt",
  salario: "briefcase",
  salud: "heart-pulse",
  transporte: "car",
};

const ACCENT_BY_CATEGORY_NAME: Record<string, string> = {
  ahorros: "#494FDF",
  alimentacion: "#00A87E",
  casa: "#EC7E00",
  comida: "#00A87E",
  comunicaciones: "#505A63",
  depositos: "#EC7E00",
  deportes: "#494FDF",
  entretenimiento: "#B09000",
  mascotas: "#00A87E",
  nomina: "#00A87E",
  ocio: "#B09000",
  otros: "#505A63",
  regalos: "#4F55F1",
  restaurante: "#494FDF",
  ropa: "#B09000",
  salario: "#00A87E",
  salud: "#E23B4A",
  transporte: "#8D969E",
};

export const CATEGORY_CHART_COLORS = {
  income: ACCENT_BY_CATEGORY_NAME.salario,
  expense: ACCENT_BY_CATEGORY_NAME.salud,
  savings: ACCENT_BY_CATEGORY_NAME.ahorros,
} as const;

const ACCENT_BY_TYPE: Record<Category["type"], string> = {
  expense: DEFAULT_ACCENT,
  income: "#00A87E",
  investment: "#EC7E00",
  transfer: "#494FDF",
};

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

function safeHexColor(value: string | null | undefined): string | null {
  if (!value) return null;
  const color = value.trim();
  return /^#[0-9a-f]{6}$/i.test(color) ? color.toUpperCase() : null;
}

function withAlpha(hexColor: string, alpha: number): string {
  const value = hexColor.slice(1);
  const red = Number.parseInt(value.slice(0, 2), 16);
  const green = Number.parseInt(value.slice(2, 4), 16);
  const blue = Number.parseInt(value.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function categoryIcon(category: CategoryVisual | null): LucideIcon {
  const configuredIcon = category?.icon?.trim().toLowerCase();
  if (configuredIcon && CATEGORY_ICONS[configuredIcon]) return CATEGORY_ICONS[configuredIcon];

  const inferredIcon = category ? ICON_BY_CATEGORY_NAME[normalize(category.name)] : undefined;
  return inferredIcon ? CATEGORY_ICONS[inferredIcon] : Tag;
}

export function getCategoryAccent(category: CategoryVisual | null): string {
  const configuredAccent = safeHexColor(category?.color);
  if (configuredAccent) return configuredAccent;
  if (!category) return DEFAULT_ACCENT;
  return ACCENT_BY_CATEGORY_NAME[normalize(category.name)]
    ?? (category.type ? ACCENT_BY_TYPE[category.type] : DEFAULT_ACCENT);
}

interface CategoryBadgeProps {
  category: CategoryVisual | null;
}

interface CategoryIconProps {
  category: CategoryVisual | null;
}

export function CategoryIcon({ category }: CategoryIconProps) {
  const accent = getCategoryAccent(category);
  const Icon = categoryIcon(category);

  return (
    <span
      aria-hidden="true"
      className="grid h-5 w-5 shrink-0 place-items-center rounded-full"
      style={{
        backgroundColor: withAlpha(accent, 0.18),
        boxShadow: `inset 0 0 0 1px ${withAlpha(accent, 0.42)}`,
      }}
    >
      <Icon size={12} strokeWidth={2.2} />
    </span>
  );
}

export default function CategoryBadge({ category }: CategoryBadgeProps) {
  const label = category?.name ?? "Sin categoría";
  const accent = getCategoryAccent(category);

  return (
    <span
      data-category-visual
      className="inline-flex max-w-[13rem] items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-medium text-[var(--text-primary)]"
      style={{
        backgroundColor: withAlpha(accent, 0.1),
        borderColor: withAlpha(accent, 0.34),
      }}
    >
      <CategoryIcon category={category} />
      <span className="truncate">{label}</span>
    </span>
  );
}
