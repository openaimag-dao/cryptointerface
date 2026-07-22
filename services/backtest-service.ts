import { ApiError, apiFetch } from "@/lib/api-client";
import type { BacktestReport, BacktestRun, BacktestRunRequest, BacktestTrade, EquityPoint } from "@/types";

export async function runBacktest(request: BacktestRunRequest): Promise<BacktestReport> {
  return apiFetch<BacktestReport>("/api/backtesting/run", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function fetchBacktestHistory(symbol?: string, limit = 20): Promise<BacktestRun[]> {
  try {
    const params = new URLSearchParams({ limit: String(limit) });
    if (symbol) params.set("symbol", symbol);
    return await apiFetch<BacktestRun[]>(`/api/backtesting/history?${params.toString()}`);
  } catch {
    return [];
  }
}

export async function fetchBacktestReport(runId: string): Promise<BacktestReport> {
  return apiFetch<BacktestReport>(`/api/backtesting/report/${runId}`);
}

export async function fetchBacktestTrades(runId: string, limit = 500): Promise<BacktestTrade[]> {
  try {
    return await apiFetch<BacktestTrade[]>(`/api/backtesting/trades/${runId}?limit=${limit}`);
  } catch {
    return [];
  }
}

export async function fetchBacktestEquity(runId: string): Promise<EquityPoint[]> {
  try {
    return await apiFetch<EquityPoint[]>(`/api/backtesting/equity/${runId}`);
  } catch {
    return [];
  }
}

export function extractErrorDetail(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      // message wasn't JSON — fall through to the raw text below
    }
    return error.message;
  }
  return error instanceof Error ? error.message : "Unknown error";
}
