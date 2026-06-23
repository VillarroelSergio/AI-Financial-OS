import { useEffect, useState } from "react";
import { fetchCategories } from "@/lib/api/categories";
import type { Category } from "@/lib/types";

export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const byId = (id: string) => categories.find((c) => c.id === id);

  return { categories, loading, byId };
}
