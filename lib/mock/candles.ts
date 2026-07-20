import type { Candle } from "@/types";

function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function getMockCandles(symbol: string, count = 180, basePrice = 64280): Candle[] {
  const seed = symbol.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const random = mulberry32(seed);
  const candles: Candle[] = [];

  let price = basePrice;
  const now = Math.floor(Date.now() / 1000);
  const intervalSeconds = 3600;

  for (let i = count; i >= 0; i -= 1) {
    const time = now - i * intervalSeconds;
    const volatility = basePrice * 0.006;
    const drift = (random() - 0.48) * volatility;
    const open = price;
    const close = Math.max(open + drift, basePrice * 0.5);
    const high = Math.max(open, close) + random() * volatility * 0.6;
    const low = Math.min(open, close) - random() * volatility * 0.6;
    const volume = 1200 + random() * 4200;

    candles.push({
      time,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume: Number(volume.toFixed(2)),
    });

    price = close;
  }

  return candles;
}
