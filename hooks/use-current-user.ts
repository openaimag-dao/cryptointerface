import { useQuery } from "@tanstack/react-query";

import { fetchCurrentUser } from "@/services/auth-client-service";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchCurrentUser,
    staleTime: 60_000,
    retry: false,
  });
}
