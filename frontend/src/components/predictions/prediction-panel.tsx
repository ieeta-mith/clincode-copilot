"use client";

import { useCodingSessionStore } from "@/stores/coding-session-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PredictionCard } from "./prediction-card";
import { PredictionSkeleton } from "@/components/shared/loading-skeleton";
import { ClipboardList } from "lucide-react";
import { useMemo } from "react";

interface PredictionPanelProps {
  isLoading: boolean;
}

export function PredictionPanel({ isLoading }: PredictionPanelProps) {
  const predictionResult = useCodingSessionStore((s) => s.predictionResult);
  const acceptedCodes = useCodingSessionStore((s) => s.acceptedCodes);
  const rejectedCodes = useCodingSessionStore((s) => s.rejectedCodes);

  const sortedPredictions = useMemo(() => {
    if (!predictionResult) return [];
    return [...predictionResult.predictions].sort((a, b) => {
      const aAccepted = acceptedCodes.has(a.code);
      const bAccepted = acceptedCodes.has(b.code);
      const aRejected = rejectedCodes.has(a.code);
      const bRejected = rejectedCodes.has(b.code);

      if (aAccepted && !bAccepted) return -1;
      if (!aAccepted && bAccepted) return 1;
      if (aRejected && !bRejected) return 1;
      if (!aRejected && bRejected) return -1;
      return a.rank - b.rank;
    });
  }, [predictionResult, acceptedCodes, rejectedCodes]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-medium text-muted-foreground">
        <ClipboardList className="h-4 w-4" />
        SUGGESTED ICD CODES
        {predictionResult && (
          <span className="ml-auto text-xs">
            {acceptedCodes.size} accepted, {rejectedCodes.size} rejected
          </span>
        )}
      </div>

      {isLoading ? (
        <PredictionSkeleton />
      ) : !predictionResult ? (
        <div className="flex flex-1 items-center justify-center p-8 text-center text-sm text-muted-foreground">
          Paste a discharge summary and click Analyze to see ICD code predictions.
        </div>
      ) : (
        <ScrollArea className="flex-1">
          <div className="space-y-2 p-4">
            {sortedPredictions.map((prediction) => (
              <PredictionCard
                key={prediction.code}
                prediction={prediction}
              />
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
