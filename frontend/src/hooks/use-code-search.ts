import { useQuery } from "@tanstack/react-query";
import { searchCodes } from "@/lib/api-client";

export function useCodeSearch(query: string) {
  return useQuery({
    queryKey: ["code-search", query],
    queryFn: () => searchCodes(query),
    enabled: query.length >= 2,
    staleTime: 60_000,
  });
}
