import { fetchCategories } from "@/lib/api/categories";
import { useAsyncData } from "@/lib/hooks/useAsyncData";
import type { Category } from "@/lib/types";

export function useCategories() {
  const { data, loading } = useAsyncData<Category[]>(fetchCategories);
  const categories = data ?? [];

  const byId = (id: string) => categories.find((c) => c.id === id);

  return { categories, loading, byId };
}
