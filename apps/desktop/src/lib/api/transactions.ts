import type { Transaction } from "@/lib/types";
import { api } from "./client";
import { buildQueryString } from "./queryParams";

export interface TransactionCreate {
  account_id: string;
  category_id?: string;
  date: string;
  description: string;
  amount: string;
  currency?: string;
  type: string;
  notes?: string;
}

export interface TransactionFilters {
  account_id?: string;
  category_id?: string;
  from_date?: string;
  to_date?: string;
  type?: string;
}

export const fetchTransactions = (filters?: TransactionFilters) =>
  api.get<Transaction[]>(`/api/transactions${buildQueryString({ ...filters })}`);

export const createTransaction = (data: TransactionCreate) =>
  api.post<Transaction>("/api/transactions", data);

export const updateTransaction = (id: string, data: Partial<TransactionCreate>) =>
  api.patch<Transaction>(`/api/transactions/${id}`, data);

export const deleteTransaction = (id: string) =>
  api.delete<void>(`/api/transactions/${id}`);
