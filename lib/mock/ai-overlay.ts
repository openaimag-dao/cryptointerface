/**
 * AI scoring/direction is out of scope for the Sprint 2 Data Engine — this
 * is a static overlay joined onto real Binance price data so the UI still
 * shows AI Score / Direction until the Sprint 3 AI module lands.
 */
import type { Direction } from "@/types";

interface AiOverlay {
  name: string;
  aiScore: number;
  direction: Direction;
}

const OVERLAY: Record<string, AiOverlay> = {
  BTCUSDT: { name: "Bitcoin", aiScore: 76, direction: "LONG" },
  ETHUSDT: { name: "Ethereum", aiScore: 54, direction: "WAIT" },
  SOLUSDT: { name: "Solana", aiScore: 88, direction: "LONG" },
  LINKUSDT: { name: "Chainlink", aiScore: 29, direction: "SHORT" },
  BNBUSDT: { name: "BNB", aiScore: 41, direction: "WAIT" },
  XRPUSDT: { name: "XRP", aiScore: 39, direction: "WAIT" },
  DOGEUSDT: { name: "Dogecoin", aiScore: 30, direction: "SHORT" },
};

export function getAiOverlay(symbol: string): AiOverlay {
  return OVERLAY[symbol] ?? { name: symbol.replace(/USDT$/, ""), aiScore: 50, direction: "WAIT" };
}
