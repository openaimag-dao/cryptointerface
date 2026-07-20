"use client";

import { useEffect, useRef } from "react";

import { WS_URL } from "@/lib/env";
import { useConnectionStore } from "@/store/connection-store";
import { useMarketStore } from "@/store/market-store";
import type { WsEnvelope } from "@/types";

const MIN_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;

/**
 * One persistent WebSocket connection to the Data Engine's `/ws/market`
 * feed, fanning out ticker/candle/funding/indicator updates into the
 * Zustand market store. Reconnects with exponential backoff on drop —
 * mirrors the resilience story on the backend's Binance connection.
 */
export function useMarketSocket(): void {
  const setWsStatus = useConnectionStore((state) => state.setWsStatus);
  const setTicker = useMarketStore((state) => state.setTicker);
  const setCandleUpdate = useMarketStore((state) => state.setCandleUpdate);
  const setFunding = useMarketStore((state) => state.setFunding);
  const setIndicators = useMarketStore((state) => state.setIndicators);

  const attemptRef = useRef(0);
  const socketRef = useRef<WebSocket | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stoppedRef = useRef(false);

  useEffect(() => {
    stoppedRef.current = false;

    function connect() {
      setWsStatus("connecting");
      const socket = new WebSocket(WS_URL);
      socketRef.current = socket;

      socket.onopen = () => {
        attemptRef.current = 0;
        setWsStatus("online");
      };

      socket.onmessage = (event: MessageEvent<string>) => {
        let envelope: WsEnvelope;
        try {
          envelope = JSON.parse(event.data) as WsEnvelope;
        } catch {
          return; // ignore malformed frames
        }

        switch (envelope.channel) {
          case "ticker":
            setTicker(envelope.data);
            break;
          case "candle":
            setCandleUpdate(envelope.data);
            break;
          case "funding":
            setFunding(envelope.data);
            break;
          case "indicators":
            setIndicators(envelope.data);
            break;
          case "trade":
            break; // not surfaced in the UI yet
        }
      };

      socket.onclose = () => {
        setWsStatus("offline");
        if (stoppedRef.current) return;
        attemptRef.current += 1;
        const delay = Math.min(
          MAX_RECONNECT_DELAY_MS,
          MIN_RECONNECT_DELAY_MS * 2 ** (attemptRef.current - 1),
        );
        timeoutRef.current = setTimeout(connect, delay);
      };

      socket.onerror = () => {
        socket.close();
      };
    }

    connect();

    return () => {
      stoppedRef.current = true;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      socketRef.current?.close();
    };
  }, [setWsStatus, setTicker, setCandleUpdate, setFunding, setIndicators]);
}
