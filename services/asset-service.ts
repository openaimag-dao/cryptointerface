import { apiFetch } from "@/lib/api-client";
import type {
  AssetAnalysis,
  AssetDerivatives,
  AssetHistory,
  AssetOverview,
  AssetSentiment,
  AssetSummary,
  AssetTechnical,
  AssetWhales,
  CorrelationReading,
  MacroInfluenceReading,
  NewsItem,
} from "@/types";

export async function fetchAssetSummary(symbol: string, interval = "1h"): Promise<AssetSummary | null> {
  try {
    return await apiFetch<AssetSummary>(`/api/assets/${symbol}?interval=${interval}`);
  } catch {
    return null;
  }
}

export async function fetchAssetOverview(symbol: string, interval = "1h"): Promise<AssetOverview | null> {
  try {
    return await apiFetch<AssetOverview>(`/api/assets/${symbol}/overview?interval=${interval}`);
  } catch {
    return null;
  }
}

export async function fetchAssetTechnical(symbol: string, interval = "1h"): Promise<AssetTechnical | null> {
  try {
    return await apiFetch<AssetTechnical>(`/api/assets/${symbol}/technical?interval=${interval}`);
  } catch {
    return null;
  }
}

export async function fetchAssetDerivatives(symbol: string): Promise<AssetDerivatives | null> {
  try {
    return await apiFetch<AssetDerivatives>(`/api/assets/${symbol}/derivatives`);
  } catch {
    return null;
  }
}

export async function fetchAssetWhales(symbol: string): Promise<AssetWhales | null> {
  try {
    return await apiFetch<AssetWhales>(`/api/assets/${symbol}/whales`);
  } catch {
    return null;
  }
}

export async function fetchAssetNews(symbol: string): Promise<NewsItem[]> {
  try {
    return await apiFetch<NewsItem[]>(`/api/assets/${symbol}/news`);
  } catch {
    return [];
  }
}

export async function fetchAssetMacro(symbol: string): Promise<MacroInfluenceReading[]> {
  try {
    return await apiFetch<MacroInfluenceReading[]>(`/api/assets/${symbol}/macro`);
  } catch {
    return [];
  }
}

export async function fetchAssetSentiment(symbol: string, interval = "1h"): Promise<AssetSentiment | null> {
  try {
    return await apiFetch<AssetSentiment>(`/api/assets/${symbol}/sentiment?interval=${interval}`);
  } catch {
    return null;
  }
}

export async function fetchAssetAnalysis(symbol: string, interval = "1h"): Promise<AssetAnalysis | null> {
  try {
    return await apiFetch<AssetAnalysis>(`/api/assets/${symbol}/analysis?interval=${interval}`);
  } catch {
    return null;
  }
}

export async function fetchAssetHistory(symbol: string, interval = "1h"): Promise<AssetHistory | null> {
  try {
    return await apiFetch<AssetHistory>(`/api/assets/${symbol}/history?interval=${interval}`);
  } catch {
    return null;
  }
}

export async function fetchAssetCorrelation(symbol: string, interval = "1h"): Promise<CorrelationReading[]> {
  try {
    return await apiFetch<CorrelationReading[]>(`/api/assets/${symbol}/correlation?interval=${interval}`);
  } catch {
    return [];
  }
}
