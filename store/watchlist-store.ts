import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface WatchlistItem {
  symbol: string; // trading pair, e.g. BTCUSDT
  pinned: boolean;
  note: string;
  addedAt: number;
}

interface WatchlistState {
  items: Record<string, WatchlistItem>;
  addSymbol: (symbol: string) => void;
  removeSymbol: (symbol: string) => void;
  togglePin: (symbol: string) => void;
  setNote: (symbol: string, note: string) => void;
  isWatched: (symbol: string) => boolean;
}

export const useWatchlistStore = create<WatchlistState>()(
  persist(
    (set, get) => ({
      items: {},
      addSymbol: (symbol) =>
        set((state) => {
          if (state.items[symbol]) return state;
          return {
            items: { ...state.items, [symbol]: { symbol, pinned: false, note: "", addedAt: Date.now() } },
          };
        }),
      removeSymbol: (symbol) =>
        set((state) => {
          const rest = { ...state.items };
          delete rest[symbol];
          return { items: rest };
        }),
      togglePin: (symbol) =>
        set((state) => {
          const item = state.items[symbol];
          if (!item) return state;
          return { items: { ...state.items, [symbol]: { ...item, pinned: !item.pinned } } };
        }),
      setNote: (symbol, note) =>
        set((state) => {
          const item = state.items[symbol];
          if (!item) return state;
          return { items: { ...state.items, [symbol]: { ...item, note } } };
        }),
      isWatched: (symbol) => Boolean(get().items[symbol]),
    }),
    { name: "aimag-watchlist-store" },
  ),
);

// Pinned first, then most-recently-added first.
export function orderedWatchlistSymbols(items: Record<string, WatchlistItem>): string[] {
  return Object.values(items)
    .sort((a, b) => Number(b.pinned) - Number(a.pinned) || b.addedAt - a.addedAt)
    .map((item) => item.symbol);
}
