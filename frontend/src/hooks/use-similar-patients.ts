import { useMutation } from "@tanstack/react-query";
import { fetchSimilarPatients } from "@/lib/api-client";
import type { SimilarPatientsRequest } from "@/lib/api-types";

export function useSimilarPatients() {
  return useMutation({
    mutationFn: (body: SimilarPatientsRequest) => fetchSimilarPatients(body),
  });
}
