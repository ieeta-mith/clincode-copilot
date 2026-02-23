"use client";

import { useCodingSessionStore } from "@/stores/coding-session-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AttentionChunk } from "./attention-chunk";
import { FileText } from "lucide-react";

export function DischargeTextViewer() {
  const predictionResult = useCodingSessionStore((s) => s.predictionResult);
  const selectedCode = useCodingSessionStore((s) => s.selectedCode);

  if (!predictionResult) return null;

  const selectedPrediction = predictionResult.predictions.find(
    (p) => p.code === selectedCode
  );

  const chunkWeights = predictionResult.chunk_texts.map((_, i) => {
    if (!selectedPrediction?.chunk_attentions) return 0;
    const attention = selectedPrediction.chunk_attentions.find(
      (a) => a.chunk_index === i
    );
    return attention?.attention_weight ?? 0;
  });

  const maxWeight = Math.max(...chunkWeights, 0);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-medium text-muted-foreground">
        <FileText className="h-4 w-4" />
        DISCHARGE SUMMARY
        <span className="ml-auto text-xs">
          {predictionResult.chunk_count} chunks
          {selectedCode && (
            <> — highlighting for <span className="font-mono font-semibold text-foreground">{selectedCode}</span></>
          )}
        </span>
      </div>
      <ScrollArea className="flex-1">
        <div className="space-y-0 p-4">
          {predictionResult.chunk_texts.map((text, i) => (
            <AttentionChunk
              key={i}
              text={text}
              weight={chunkWeights[i]}
              maxWeight={maxWeight}
              index={i}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
