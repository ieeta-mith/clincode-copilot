"use client";

import { Button } from "@/components/ui/button";
import { ScoreBadge } from "@/components/shared/score-badge";
import { PredictionScoreBar } from "./prediction-score-bar";
import { Check, X, RotateCcw } from "lucide-react";
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
  const acceptedCodes = useCodingSessionStore((s) => s.acceptedCodes);
  const rejectedCodes = useCodingSessionStore((s) => s.rejectedCodes);
  const acceptCode = useCodingSessionStore((s) => s.acceptCode);
  const rejectCode = useCodingSessionStore((s) => s.rejectCode);
  const resetCodeDecision = useCodingSessionStore((s) => s.resetCodeDecision);

  const isSelected = selectedCode === prediction.code;
  const isAccepted = acceptedCodes.has(prediction.code);
  const isRejected = rejectedCodes.has(prediction.code);

  return (
    <div
      className={cn(
        "cursor-pointer rounded-lg border p-3 transition-all hover:shadow-sm",
        isSelected && "border-primary ring-1 ring-primary",
        isAccepted && "border-emerald-300 bg-emerald-50",
        isRejected && "border-muted bg-muted/50 opacity-60"
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
          <p className="mt-1 truncate text-sm text-muted-foreground">
            {prediction.description}
          </p>
        </div>
      </div>

      <PredictionScoreBar score={prediction.score} className="mt-2" />

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

      <div className="mt-2 flex gap-1.5">
        {isAccepted || isRejected ? (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              resetCodeDecision(prediction.code);
            }}
          >
            <RotateCcw className="h-3 w-3" />
            Undo
          </Button>
        ) : (
          <>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs text-emerald-600 hover:bg-emerald-50 hover:text-emerald-700"
              onClick={(e) => {
                e.stopPropagation();
                acceptCode(prediction.code);
              }}
            >
              <Check className="h-3 w-3" />
              Accept
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={(e) => {
                e.stopPropagation();
                rejectCode(prediction.code);
              }}
            >
              <X className="h-3 w-3" />
              Reject
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
