import type { Account } from "@/lib/types";
import { api } from "./client";

export interface AccountCreate {
  name: string;
  type: string;
  institution?: string;
  currency?: string;
  current_balance?: string;
}

export interface AccountUpdate {
  name?: string;
  type?: string;
  institution?: string;
  currency?: string;
  current_balance?: string;
  is_active?: boolean;
}

export const fetchAccounts = () => api.get<Account[]>("/api/accounts");
export const createAccount = (data: AccountCreate) => api.post<Account>("/api/accounts", data);
export const updateAccount = (id: string, data: AccountUpdate) =>
  api.patch<Account>(`/api/accounts/${id}`, data);
export const deleteAccount = (id: string) => api.delete<void>(`/api/accounts/${id}`);
