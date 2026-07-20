import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

import type { CandleUpdateMessage, FundingRateData, IndicatorSnapshot, TickerUpdateMessage } from "@/types";

interface MarketState {
  tickers: Record<string, TickerUpdateMessage>;
  candleUpdates: Record<string, CandleUpdateMessage>; // key: `${symbol}:${interval}`
  funding: Record<string, FundingRateData>;
  indicators: Record<string, IndicatorSnapshot>; // key: `${symbol}:${interval}`
  setTicker: (update: TickerUpdateMessage) => void;
  setCandleUpdate: (update: CandleUpdateMessage) => void;
  setFunding: (update: FundingRateData) => void;
  setIndicators: (snapshot: IndicatorSnapshot) => void;
}

export const candleKey = (symbol: string, interval: string): string => `${symbol}:${interval}`;

export const useMarketStore = create<MarketState>()(
  subscribeWithSelector((set) => ({
    tickers: {},
    candleUpdates: {},
    funding: {},
    indicators: {},

    setTicker: (update) =>
      set((state) => ({ tickers: { ...state.tickers, [update.symbol]: update } })),

    setCandleUpdate: (update) =>
      set((state) => ({
        candleUpdates: { ...state.candleUpdates, [candleKey(update.symbol, update.interval)]: update },
      })),

    setFunding: (update) =>
      set((state) => ({ funding: { ...state.funding, [update.symbol]: update } })),

    setIndicators: (snapshot) =>
      set((state) => ({
        indicators: { ...state.indicators, [candleKey(snapshot.symbol, snapshot.interval)]: snapshot },
      })),
  })),
);
