"use client";

import { useCodingSessionStore } from "@/stores/coding-session-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PredictionCard } from "./prediction-card";
import { PredictionSkeleton } from "@/components/shared/loading-skeleton";
import { ClipboardList } from "lucide-react";

interface PredictionPanelProps {
  isLoading: boolean;
}

export function PredictionPanel({ isLoading }: PredictionPanelProps) {
  const predictionResult = useCodingSessionStore((s) => s.predictionResult);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-medium text-muted-foreground">
        <ClipboardList className="h-4 w-4" />
        SUGGESTED ICD CODES
        {predictionResult && (
          <span className="ml-auto text-xs">
            {predictionResult.predictions.length} codes
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
        <ScrollArea className="flex-1 min-h-0">
          <div className="space-y-2 p-4">
            {predictionResult.predictions.map((prediction) => (
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
