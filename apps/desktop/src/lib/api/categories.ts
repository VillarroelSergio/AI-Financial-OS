import type { Category } from "@/lib/types";
import { api } from "./client";

export interface CategoryCreate {
  name: string;
  type: string;
  parent_id?: string;
  icon?: string;
  color?: string;
}

export const fetchCategories = () => api.get<Category[]>("/api/categories");
export const createCategory = (data: CategoryCreate) =>
  api.post<Category>("/api/categories", data);
