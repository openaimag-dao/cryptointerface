import { useQuery } from "@tanstack/react-query";

import { fetchNews } from "@/services/news-service";

export function useNews() {
  return useQuery({
    queryKey: ["news"],
    queryFn: fetchNews,
    refetchInterval: 60_000,
  });
}
