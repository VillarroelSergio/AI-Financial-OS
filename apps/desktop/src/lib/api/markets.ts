import type { MarketQuote } from "@/lib/types";
import { api } from "./client";

export const getQuotes = (category?: string) =>
  api.get<MarketQuote[]>(
    `/api/markets/quotes${category ? `?category=${category}` : ""}`
  );
