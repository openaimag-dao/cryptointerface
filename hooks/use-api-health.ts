"use client";

import { useEffect } from "react";

import { apiFetch } from "@/lib/api-client";
import { useConnectionStore } from "@/store/connection-store";

const POLL_INTERVAL_MS = 15_000;

/** Polls the backend's health endpoint to drive the header's "API" status pill. */
export function useApiHealthPoll(): void {
  const setApiStatus = useConnectionStore((state) => state.setApiStatus);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      setApiStatus("connecting");
      try {
        await apiFetch<{ status: string }>("/api/health");
        if (!cancelled) setApiStatus("online");
      } catch {
        if (!cancelled) setApiStatus("offline");
      }
    }

    check();
    const interval = setInterval(check, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [setApiStatus]);
}
