import type { AiSignal, Direction } from "@/types";

const REASON_POOL: Record<Direction, string[]> = {
  LONG: [
    "Price reclaimed the daily VWAP with rising volume",
    "RSI bullish divergence confirmed on the 4H chart",
    "Funding rate reset to neutral after long liquidations",
    "Order book shows strong bid absorption at support",
    "On-chain exchange outflows accelerating (accumulation)",
    "50/200 EMA golden cross on the higher timeframe",
  ],
  SHORT: [
    "Rejection at key resistance with bearish engulfing candle",
    "Funding rate overheated, crowded long positioning",
    "Open interest spiking without price confirmation",
    "Whale wallets moving supply onto exchanges",
    "RSI bearish divergence on the 1H timeframe",
    "Liquidity cluster of stop-losses building below price",
  ],
  WAIT: [
    "Price is consolidating inside a tight range",
    "Conflicting signals between momentum and volume",
    "Macro event risk in the next 24 hours (FOMC/CPI)",
    "Low liquidity conditions, wider than usual spreads",
    "Awaiting confirmation candle beyond range boundaries",
  ],
};

function pickReasons(direction: Direction, count: number): string[] {
  const pool = [...REASON_POOL[direction]];
  const picked: string[] = [];
  while (picked.length < count && pool.length > 0) {
    const index = Math.floor(Math.random() * pool.length);
    picked.push(pool.splice(index, 1)[0]);
  }
  return picked;
}

const SIGNAL_SEEDS: { symbol: string; direction: Direction; entry: number; confidence: number }[] = [
  { symbol: "SOLUSDT", direction: "LONG", entry: 172.4, confidence: 88 },
  { symbol: "BTCUSDT", direction: "LONG", entry: 64280, confidence: 76 },
  { symbol: "ETHUSDT", direction: "WAIT", entry: 3412, confidence: 54 },
  { symbol: "LINKUSDT", direction: "SHORT", entry: 18.62, confidence: 71 },
  { symbol: "AVAXUSDT", direction: "LONG", entry: 38.4, confidence: 82 },
  { symbol: "DOGEUSDT", direction: "SHORT", entry: 0.1523, confidence: 66 },
];

export function getMockSignals(): AiSignal[] {
  return SIGNAL_SEEDS.map((seed, index) => {
    const riskUnit = seed.entry * 0.018;
    const stopLoss = seed.direction === "SHORT" ? seed.entry + riskUnit : seed.entry - riskUnit;
    const tpDirectionMultiplier = seed.direction === "SHORT" ? -1 : 1;

    return {
      id: `sig-${index}-${seed.symbol}`,
      symbol: seed.symbol,
      direction: seed.direction,
      confidence: seed.confidence,
      entry: seed.entry,
      stopLoss: Number(stopLoss.toFixed(4)),
      takeProfit1: Number((seed.entry + tpDirectionMultiplier * riskUnit * 1.5).toFixed(4)),
      takeProfit2: Number((seed.entry + tpDirectionMultiplier * riskUnit * 2.5).toFixed(4)),
      takeProfit3: Number((seed.entry + tpDirectionMultiplier * riskUnit * 4).toFixed(4)),
      riskReward: Number((2 + (index % 3)).toFixed(1)),
      reasons: pickReasons(seed.direction, 3),
      createdAt: new Date(Date.now() - index * 1000 * 60 * 37).toISOString(),
      timeframe: ["15m", "1H", "4H"][index % 3],
    };
  });
}
