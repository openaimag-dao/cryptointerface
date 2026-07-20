import type { WhaleTransaction, WhaleTxType } from "@/types";

const TYPES: WhaleTxType[] = ["TRANSFER", "DEPOSIT", "WITHDRAWAL", "SWAP"];
const SYMBOLS = ["BTC", "ETH", "SOL", "USDT", "LINK"];
const EXCHANGES = ["Binance", "Coinbase", "OKX", "Bybit", null];

function shortAddress(seed: number): string {
  return `0x${(seed * 291 + 173).toString(16).padStart(6, "0").slice(0, 6)}...${(seed * 71).toString(16).slice(0, 4)}`;
}

export function getMockWhaleTransactions(count = 24): WhaleTransaction[] {
  return Array.from({ length: count }, (_, index) => {
    const symbol = SYMBOLS[index % SYMBOLS.length];
    const type = TYPES[index % TYPES.length];
    const amount = 50 + ((index * 137) % 900);
    const price = symbol === "BTC" ? 64280 : symbol === "ETH" ? 3412 : symbol === "SOL" ? 172 : symbol === "USDT" ? 1 : 18.6;

    return {
      id: `whale-${index}`,
      symbol,
      type,
      amount,
      amountUsd: Math.round(amount * price * (symbol === "BTC" ? 10 : symbol === "USDT" ? 8000 : 300)),
      from: shortAddress(index),
      to: shortAddress(index + 91),
      exchange: EXCHANGES[index % EXCHANGES.length],
      timestamp: new Date(Date.now() - index * 1000 * 60 * 14).toISOString(),
      txHash: `0x${(index * 928371 + 5555).toString(16).padStart(10, "0")}`,
    };
  });
}
