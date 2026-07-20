import { useQuery } from "@tanstack/react-query";

import { fetchMacroEvents, fetchMacroIndicators } from "@/services/macro-service";

export function useMacroIndicators() {
  return useQuery({
    queryKey: ["macro-indicators"],
    queryFn: fetchMacroIndicators,
  });
}

export function useMacroEvents() {
  return useQuery({
    queryKey: ["macro-events"],
    queryFn: fetchMacroEvents,
  });
}
