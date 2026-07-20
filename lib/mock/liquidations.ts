import type { LiquidationEvent, LiquidationHeatmapCell } from "@/types";

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT"];
const EXCHANGES = ["Binance", "OKX", "Bybit", "Bitget"];

export function getMockLiquidations(count = 30): LiquidationEvent[] {
  return Array.from({ length: count }, (_, index) => {
    const symbol = SYMBOLS[index % SYMBOLS.length];
    const side = index % 3 === 0 ? "SHORT" : "LONG";
    const amountUsd = 8_000 + ((index * 2917) % 480_000);
    const basePrice = symbol === "BTCUSDT" ? 64280 : symbol === "ETHUSDT" ? 3412 : symbol === "SOLUSDT" ? 172 : symbol === "LINKUSDT" ? 18.6 : 38.4;

    return {
      id: `liq-${index}`,
      symbol,
      side,
      amountUsd,
      price: Number((basePrice * (1 + ((index % 7) - 3) / 500)).toFixed(2)),
      exchange: EXCHANGES[index % EXCHANGES.length],
      timestamp: new Date(Date.now() - index * 1000 * 60 * 6).toISOString(),
    };
  });
}

export function getMockLiquidationHeatmap(basePrice = 64280, count = 40): LiquidationHeatmapCell[] {
  return Array.from({ length: count }, (_, index) => {
    const offset = (index - count / 2) * (basePrice * 0.0025);
    const distanceFactor = Math.abs(index - count / 2) / (count / 2);
    return {
      price: Number((basePrice + offset).toFixed(2)),
      intensity: Number(Math.max(0.08, 1 - distanceFactor + Math.sin(index) * 0.15).toFixed(2)),
    };
  });
}

export const LIQUIDATION_TOTALS_24H = {
  longUsd: 182_400_000,
  shortUsd: 96_700_000,
};
