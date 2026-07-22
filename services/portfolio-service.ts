import { apiFetch } from "@/lib/api-client";
import type { PortfolioSummary } from "@/types";

export async function fetchPortfolio(): Promise<PortfolioSummary> {
  return apiFetch<PortfolioSummary>("/api/portfolio");
}
