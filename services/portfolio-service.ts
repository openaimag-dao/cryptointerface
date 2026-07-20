import { getMockPortfolio } from "@/lib/mock/portfolio";
import { mockDelay } from "@/lib/mock/delay";
import type { PortfolioSummary } from "@/types";

export async function fetchPortfolio(): Promise<PortfolioSummary> {
  return mockDelay(getMockPortfolio());
}
