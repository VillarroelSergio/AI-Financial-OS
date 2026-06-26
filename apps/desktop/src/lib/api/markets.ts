import type { MarketQuote } from "@/lib/types";
import { api } from "./client";

export const getQuotes = () =>
  api.get<MarketQuote[]>("/api/markets/quotes");

export const refreshQuotes = () =>
  api.post<MarketQuote[]>("/api/markets/quotes/refresh", {});
