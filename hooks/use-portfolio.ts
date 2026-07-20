import { useQuery } from "@tanstack/react-query";

import { fetchPortfolio } from "@/services/portfolio-service";

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: fetchPortfolio,
  });
}
