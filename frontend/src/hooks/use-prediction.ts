import { useMutation } from "@tanstack/react-query";
import { predictDetailed } from "@/lib/api-client";
import type { PredictionRequest } from "@/lib/api-types";

export function usePrediction() {
  return useMutation({
    mutationFn: (body: PredictionRequest) => predictDetailed(body),
  });
}
