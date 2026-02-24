"use client";

import { ScoreBadge } from "@/components/shared/score-badge";
import { useCodingSessionStore } from "@/stores/coding-session-store";
import { cn } from "@/lib/utils";
import type { DetailedICDPrediction } from "@/lib/api-types";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PredictionCardProps {
  prediction: DetailedICDPrediction;
}

export function PredictionCard({ prediction }: PredictionCardProps) {
  const selectedCode = useCodingSessionStore((s) => s.selectedCode);
  const selectCode = useCodingSessionStore((s) => s.selectCode);

  const isSelected = selectedCode === prediction.code;

  return (
    <div
      className={cn(
        "cursor-pointer rounded-lg border p-3 transition-all hover:shadow-sm",
        isSelected && "border-primary ring-1 ring-primary"
      )}
      onClick={() => selectCode(prediction.code)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-semibold">
              {prediction.code}
            </span>
            <ScoreBadge score={prediction.score} />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {prediction.description}
          </p>
        </div>
      </div>

      <div className="mt-2 flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="text-xs text-muted-foreground">
              LA: {(prediction.la_score * 100).toFixed(1)}%
            </span>
          </TooltipTrigger>
          <TooltipContent>Label Attention score</TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="text-xs text-muted-foreground">
              KNN: {(prediction.knn_score * 100).toFixed(1)}%
            </span>
          </TooltipTrigger>
          <TooltipContent>KNN similarity score</TooltipContent>
        </Tooltip>
      </div>

    </div>
  );
}
